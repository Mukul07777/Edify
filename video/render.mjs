// Photographs video.html frame by frame and joins the frames with the sound track.
//   node render.mjs --still 5,12.5,40        a few moments as PNGs in stills/ (to check the picture)
//   node render.mjs                          every frame into frames/, then out/edify-demo-<voice>.mp4 for each voice
//   node render.mjs --encode                 only join frames already made
import { execFileSync, spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "../frontend/node_modules/playwright/index.mjs";

const args = process.argv.slice(2), flag = (n) => args.includes(n), val = (n) => (args.includes(n) ? args[args.indexOf(n) + 1] : null);
const DATA = JSON.parse(fs.readFileSync("data.js", "utf8").replace(/^window\.DATA = /, "").replace(/;\s*$/, ""));
const FPS = DATA.fps, FRAMES = Math.floor(DATA.total * FPS), WORKERS = +(val("--workers") || 3);
const url = pathToFileURL(path.resolve("video.html")).href + "?raw=1";
const FFMPEG = process.env.FFMPEG || execFileSync(process.env.VTOOLS_PY || "python", ["-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"], { encoding: "utf8" }).trim();

async function open(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on("pageerror", (e) => console.log("PAGE ERROR:", e.message));
  page.on("console", (m) => m.type() === "error" && console.log("console:", m.text()));
  await page.goto(url);
  await page.evaluate(() => window.ready);
  return page;
}

if (flag("--still")) {
  fs.mkdirSync("stills", { recursive: true });
  const browser = await chromium.launch({ channel: "msedge" });
  const page = await open(browser);
  for (const t of val("--still").split(",").map(Number)) {
    await page.evaluate((t) => window.seek(t), t);
    await page.screenshot({ path: `stills/t${String(t.toFixed(1)).padStart(5, "0")}.jpg`, type: "jpeg", quality: 82 });
  }
  await browser.close();
  process.exit(0);
}

if (!flag("--encode")) {
  fs.mkdirSync("frames", { recursive: true });
  const from = +(val("--from") || 0) * FPS | 0, to = val("--to") ? Math.min(FRAMES, +val("--to") * FPS | 0) : FRAMES;
  const browser = await chromium.launch({ channel: "msedge" });
  const per = Math.ceil((to - from) / WORKERS), t0 = Date.now();
  let done = 0;
  await Promise.all(Array.from({ length: WORKERS }, async (_, w) => {
    const page = await open(browser);
    for (let f = from + w * per; f < Math.min(to, from + (w + 1) * per); f++) {
      await page.evaluate((t) => window.seek(t), f / FPS);
      await page.screenshot({ path: `frames/f_${String(f).padStart(5, "0")}.jpg`, type: "jpeg", quality: 94 });
      if (++done % 300 === 0) console.log(`${done}/${to - from} frames, ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    await page.close();
  }));
  await browser.close();
  console.log(`frames done in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
}

if (!val("--to") && !val("--from")) {
  fs.mkdirSync("out", { recursive: true });
  for (const voice of ["male"]) {
    const out = `out/edify-demo-${voice}-voice.mp4`;
    const r = spawnSync(FFMPEG, ["-y", "-v", "error", "-framerate", String(FPS), "-i", "frames/f_%05d.jpg", "-i", `audio/${voice}.wav`,
      "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], { stdio: "inherit" });
    console.log(out, r.status === 0 ? `${(fs.statSync(out).size / 1e6).toFixed(1)} MB` : "FAILED");
  }
}
