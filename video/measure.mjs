// Where the cards the video points at sit on each filmed screen (CSS px, in the tall picture's coordinates).
//   node measure.mjs     -> shots/rects.json
import fs from "node:fs";
import { chromium } from "../frontend/node_modules/playwright/index.mjs";

const BASE = "http://127.0.0.1:8011", PW = "focs-demo-2026";
const meta = JSON.parse(fs.readFileSync("shots/shots.json", "utf8"));
const login = async (key) => (await fetch(`${BASE}/api/auth/login`, { method: "POST", headers: { "content-type": "application/json" },
  body: JSON.stringify({ email: `demo.focs.${key}@example.com`, password: PW }) })).json();
const api = async (token, path) => (await fetch(BASE + "/api" + path, { headers: { Authorization: `Bearer ${token}` } })).json().catch(() => null);
const browser = await chromium.launch({ channel: "msedge" });
const out = {};

async function measure(key, shot, path, targets) {
  const a = await login(key);
  const ctx = await browser.newContext({ viewport: { width: 1440, height: meta[shot].tallH } });
  await ctx.addInitScript((a) => {
    localStorage.setItem("focs-auth", JSON.stringify({ state: { token: a.access_token, user: a.user }, version: 0 }));
    localStorage.setItem(`focs.tour.done.${a.user.id}`, "1");
  }, a);
  const page = await ctx.newPage();
  await page.goto(BASE + (typeof path === "function" ? await path(a.access_token) : path));
  await page.waitForLoadState("networkidle").catch(() => {});
  await page.waitForTimeout(2200);
  if (shot === "s_genome_focus") {
    await page.locator("svg g", { has: page.locator("title", { hasText: /^Electricity \(/ }) }).first().click({ force: true });
    await page.waitForTimeout(400);
  }
  out[shot] = await page.evaluate((targets) => {
    const res = {};
    for (const [name, source, minW, nth] of targets) {
      const re = new RegExp(source, "i");
      const hits = [...document.querySelectorAll("body *")].filter((el) => el.children.length < 4 && re.test((el.textContent || "").trim()) &&
        ![...el.children].some((c) => re.test((c.textContent || "").trim())));
      let el = hits[nth || 0];
      if (!el) { res[name] = null; continue; }
      while (el.parentElement) {   // climb to the card: rounded, and at least minW wide
        const r = el.getBoundingClientRect();
        if (r.width >= minW && (minW === 0 || parseFloat(getComputedStyle(el).borderTopLeftRadius) >= 8)) break;
        el = el.parentElement;
      }
      const r = el.getBoundingClientRect();
      res[name] = { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
    }
    return res;
  }, targets);
  console.log(shot, JSON.stringify(out[shot]));
  await ctx.close();
}

await measure("student", "s_roots", "/app/roots", [["noticed", "^Edify noticed$", 500], ["noticed2", "^Edify noticed$", 500, 1], ["btn", "Check it in 2 minutes", 0], ["chips", "From your weak spots", 500]]);
await measure("video", "v_after", `/app/roots?trace=${meta.v_trace.id}`, [["stuck", "You're stuck on", 500], ["first", "^First, ", 500], ["root", "^Root gap$", 500],
  ["link2", "Solving systems of linear equations", 500], ["link3", "Understanding direct and inverse", 500], ["real", "^The real gap:", 500],
  ["lesson", "Everyday Example", 400], ["closed", "Gap closed", 0], ["ba", "before and after$", 500], ["score", "^3/3$", 0]]);
await measure("classmate", "c_dash", "/app", [["coach", "re-plans every night", 600], ["fix", "^Fix the root", 300], ["stats", "Study streak", 150]]);
await measure("teacher", "t_class", async (t) => `/app/classes/${(await api(t, "/classes")).teaching[0].id}`,
  [["stuck", "^Where the class is stuck$", 600], ["gaps", "^Where the gaps really start$", 600], ["teach", "^Teach first", 400], ["students", "^Students$", 600, 1]]);
await measure("teacher", "t_report", async (t) => `/app/rooms/${(await api(t, "/rooms"))[0].code}/report`,
  [["boards", "^The boards that lost the room$", 600], ["stats", "I'm lost taps", 150], ["quiz", "^Pop quizzes$", 300], ["doubts", "^Top doubts$", 300]]);
await measure("student", "s_genome_focus", "/app/genome", [["map", "^The map$", 600], ["top", "^Most load-bearing school chapters$", 600], ["stat", "Exam chapters mapped", 150], ["load", "Load-bearing chapter", 600]]);
await measure("student", "s_session", async (t) => `/app/library/${(await api(t, "/sessions"))[0].id}`,
  [["sheet", "^Revision sheet$", 400], ["key", "^Key points$", 400], ["formula", "^Formula sheet$", 400], ["check", "^Quick self-check$", 400], ["note1", "^On the board$", 400], ["ask", "Ask about this lecture", 200]]);
await measure("student", "s_weak", "/app/weak", [["plan", "^Current Electricity$", 400], ["tests", "Tumhare tests", 200]]);
await measure("student", "s_dash", "/app", [["watch", "Aaj lecture dekh rahe ho", 500]]);
fs.writeFileSync("shots/rects.json", JSON.stringify(out, null, 1));
await browser.close();
