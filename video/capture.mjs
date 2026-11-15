// Films the real app for the demo video: every screen at 2x, tall pages in full, the trace flow step by step.
//   node capture.mjs [parts]     (the app on http://127.0.0.1:8011, demo accounts seeded, setup_account.py run)
//   parts: hero,landing,student,trace,trace10,others,dark,phone (default: all)
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import { chromium } from "../frontend/node_modules/playwright/index.mjs";

const BASE = "http://127.0.0.1:8011", PW = "focs-demo-2026", VW = 1440, VH = 810;
const ONLY = process.argv[2] ? new Set(process.argv[2].split(",")) : null;
const want = (part) => !ONLY || ONLY.has(part);
const meta = fs.existsSync("shots/shots.json") ? JSON.parse(fs.readFileSync("shots/shots.json", "utf8")) : {};
const save = () => fs.writeFileSync("shots/shots.json", JSON.stringify(meta, null, 1));
const login = async (key) => (await fetch(`${BASE}/api/auth/login`, { method: "POST", headers: { "content-type": "application/json" },
  body: JSON.stringify({ email: `demo.focs.${key}@example.com`, password: PW }) })).json();
const api = async (token, path) => (await fetch(BASE + "/api" + path, { headers: { Authorization: `Bearer ${token}` } })).json().catch(() => null);
const browser = await chromium.launch({ channel: "msedge" });

async function ctxFor(key, { dark = false, vw = VW, vh = VH, dpr = 2, mobile = false } = {}) {
  const a = key ? await login(key) : null;
  const ctx = await browser.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: dpr, isMobile: mobile, hasTouch: mobile });
  await ctx.addInitScript(([a, dark]) => {
    if (a) {
      localStorage.setItem("focs-auth", JSON.stringify({ state: { token: a.access_token, user: a.user }, version: 0 }));
      localStorage.setItem(`focs.tour.done.${a.user.id}`, "1");
    }
    if (dark) localStorage.setItem("focs-look-4", "dark");
  }, [a, dark]);
  return { ctx, token: a?.access_token, vw, vh };
}

const QUIET = "*::-webkit-scrollbar{display:none!important} *{scrollbar-width:none!important} [data-sonner-toaster]{display:none!important}";
async function settle(page, ms = 1200) {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page.addStyleTag({ content: QUIET }).catch(() => {});
  await page.waitForTimeout(ms);
}

/** The viewport as it is (the shell), then the whole page with the viewport grown to fit the inner scroller. */
async function snap(page, name, { vw = VW, vh = VH, maxTall = 5200 } = {}) {
  const region = await page.evaluate(() => {
    let best = null;
    for (const el of document.querySelectorAll("main, div, section")) {
      const s = getComputedStyle(el);
      if (!/(auto|scroll)/.test(s.overflowY) || el.scrollHeight <= el.clientHeight + 8) continue;
      const r = el.getBoundingClientRect();
      if (r.width < innerWidth * 0.5) continue;
      if (!best || r.width * r.height > best.area) best = { area: r.width * r.height, x: r.x, y: r.y, w: r.width, h: r.height, sh: el.scrollHeight, ch: el.clientHeight };
    }
    const doc = document.documentElement;
    if (!best && doc.scrollHeight > innerHeight + 8) best = { x: 0, y: 0, w: innerWidth, h: innerHeight, sh: doc.scrollHeight, ch: innerHeight, win: true };
    return best;
  });
  await page.screenshot({ path: `shots/${name}.png` });
  const m = { w: vw, h: vh, tallH: vh, region: region ? { x: region.x, y: region.y, w: region.w, h: region.h } : null };
  if (region) {
    const tallH = Math.min(maxTall, vh + (region.sh - region.ch));
    await page.setViewportSize({ width: vw, height: tallH });
    await page.waitForTimeout(700);
    await page.screenshot({ path: `shots/${name}_tall.png` });
    await page.setViewportSize({ width: vw, height: vh });
    await page.waitForTimeout(300);
    m.tallH = tallH;
  }
  meta[name] = m; save();
  console.log(name, m.tallH);
}

async function visit(c, name, path, opts = {}) {
  const page = await c.ctx.newPage();
  await page.goto(BASE + path).catch(() => {});
  await settle(page, opts.wait ?? 1600);
  if (opts.before) await opts.before(page);
  await snap(page, name, { vw: c.vw, vh: c.vh, ...opts });
  await page.close();
}

// ------------------------------------------------------------------ landing: its live hero as a flipbook, then the whole page
if (want("hero")) {
  const c = await ctxFor(null, { vw: 1440, vh: 1100, dpr: 1.25 });
  const page = await c.ctx.newPage();
  await page.goto(BASE + "/"); await settle(page, 400);
  await page.evaluate(() => scrollTo(0, 190)); await page.waitForTimeout(300);
  fs.mkdirSync("shots/hero", { recursive: true });
  const t0 = Date.now(), times = [];
  for (let i = 0; i < 110; i++) {
    await page.screenshot({ path: `shots/hero/${String(i).padStart(3, "0")}.jpg`, type: "jpeg", quality: 90 });
    times.push(Date.now() - t0);
    await page.waitForTimeout(25);
  }
  meta.hero = { frames: 110, times, w: 1440, h: 1100 }; save();
  console.log("hero", times.at(-1), "ms");
  await c.ctx.close();
}
if (want("landing")) {
  const c = await ctxFor(null);
  const page = await c.ctx.newPage();
  await page.goto(BASE + "/"); await settle(page, 600);
  // every section revealed (they fade in on scroll) before the full-page picture
  const h = await page.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < h; y += 500) { await page.evaluate((y) => scrollTo(0, y), y); await page.waitForTimeout(140); }
  await page.evaluate(() => scrollTo(0, 0)); await page.waitForTimeout(500);
  await page.screenshot({ path: "shots/landing.png" });
  await page.screenshot({ path: "shots/landing_tall.jpg", fullPage: true, type: "jpeg", quality: 90 });
  meta.landing = { w: VW, h: VH, tallH: h, region: { x: 0, y: 0, w: VW, h: VH }, tallExt: "jpg" }; save();
  await c.ctx.close();
}
if (want("trace10")) {   // the demo student's finished trace, light and dark
  const c = await ctxFor("student"); await visit(c, "s_trace10", "/app/roots?trace=10"); await c.ctx.close();
  const d = await ctxFor("student", { dark: true }); await visit(d, "d_trace", "/app/roots?trace=10"); await d.ctx.close();
}

// ------------------------------------------------------------------ the student's screens
if (want("student")) {
  const c = await ctxFor("student");
  const sessions = await api(c.token, "/sessions");
  const pages = [["s_dash", "/app"], ["s_studio", "/app/studio"], ["s_library", "/app/library"], ["s_session", `/app/library/${sessions?.[0]?.id}`],
    ["s_flash", "/app/flashcards"], ["s_formulas", "/app/formulas"], ["s_weak", "/app/weak"], ["s_mock", "/app/mock"], ["s_revise", "/app/revise"],
    ["s_practice", "/app/practice"], ["s_prep", "/app/prep"], ["s_snap", "/app/snap"], ["s_rooms", "/app/rooms"], ["s_campus", "/app/campus"],
    ["s_mentors", "/app/mentors"], ["s_settings", "/app/settings"], ["s_roots", "/app/roots"], ["s_trace10", "/app/roots?trace=10"], ["s_genome", "/app/genome"]];
  for (const [n, p] of pages) await visit(c, n, p);
  await visit(c, "s_genome_focus", "/app/genome", { before: async (page) => {
    await page.locator("svg g", { has: page.locator("title", { hasText: /^Electricity \(/ }) }).first().click({ force: true }).catch((e) => console.log("focus failed", e.message));
    await page.waitForTimeout(500);
  } });
  await c.ctx.close();
}

// ------------------------------------------------------------------ the trace, step by step (the throwaway account)
if (want("trace")) {
  const c = await ctxFor("video");
  const page = await c.ctx.newPage();
  const answers = (id) => JSON.parse(execFileSync("python", ["../video/answers.py", String(id)], { cwd: "../backend", encoding: "utf8" }).trim().split("\n").at(-1));
  const groups = () => page.locator("div.mt-3.grid.gap-2");
  const pick = async (g, i) => { await groups().nth(g).locator("button").nth(i).click(); await page.waitForTimeout(120); };
  const wrong = (a, n = 4) => (a + 1) % n;
  await page.goto(BASE + "/app/roots"); await settle(page, 1800);
  await snap(page, "v_noticed");
  await page.getByRole("button", { name: /Check it in 2 minutes/ }).first().click();
  await page.waitForURL(/trace=\d+/); await settle(page, 1500);
  const id = Number(new URL(page.url()).searchParams.get("trace"));
  await snap(page, "v_check");
  const a = answers(id);
  console.log("trace", id, JSON.stringify(a));
  const nb = a.before.length;
  for (let i = 0; i < nb; i++) await pick(i, i === 0 ? a.before[i] : wrong(a.before[i]));           // the stuck topic: 1 of 3 right
  for (let i = 0; i < a.chain.length; i++) {
    const miss = a.chapters[i] === "c10.science.electricity";                                           // the idea this student is missing
    await pick(nb + i, miss ? 0 : a.chain[i]);                                                          // "It doubles": the classic slip
  }
  await page.waitForTimeout(400);
  await snap(page, "v_answered");
  await page.getByRole("button", { name: /Find my root gap/ }).click();
  await page.getByText(/The real gap:/).waitFor({ timeout: 60000 }); await settle(page, 900);
  await snap(page, "v_found");
  await page.getByRole("button", { name: /Fix it in 5 minutes/ }).click();
  await page.getByRole("button", { name: /^Check$/ }).waitFor({ timeout: 180000 }); await settle(page, 1200);
  await snap(page, "v_lesson", { maxTall: 7000 });
  const b = answers(id);
  const lessonGroup = nb + a.chain.length;
  await pick(lessonGroup, b.lesson);
  await page.getByRole("button", { name: /^Check$/ }).click();
  await page.getByText(/Gap closed/).waitFor({ timeout: 60000 }); await settle(page, 900);
  await snap(page, "v_fixed", { maxTall: 7000 });
  const d = answers(id);
  for (let i = 0; i < d.after.length; i++) await pick(lessonGroup + 1 + i, d.after[i]);
  await page.getByRole("button", { name: /See the difference/ }).click();
  await page.getByText(/before and after/i).waitFor({ timeout: 60000 }); await settle(page, 900);
  await snap(page, "v_after", { maxTall: 7600 });
  meta.v_trace = { id }; save();
  await visit(c, "v_dash", "/app");
  await c.ctx.close();
}

// ------------------------------------------------------------------ Hindi student, teacher, classmate's coach
if (want("others")) {
  const h = await ctxFor("hindi");
  const hs = await api(h.token, "/sessions");
  await visit(h, "h_dash", "/app"); await visit(h, "h_session", `/app/library/${hs?.[0]?.id}`); await visit(h, "h_roots", "/app/roots");
  await h.ctx.close();
  const t = await ctxFor("teacher");
  const classes = await api(t.token, "/classes"), rooms = await api(t.token, "/rooms");
  await visit(t, "t_class", `/app/classes/${classes?.teaching?.[0]?.id}`, { wait: 2500 });
  await visit(t, "t_report", `/app/rooms/${rooms?.[0]?.code}/report`, { wait: 2500 });
  await t.ctx.close();
  const c = await ctxFor("classmate");
  await visit(c, "c_dash", "/app", { wait: 3000 });
  await c.ctx.close();
}

// ------------------------------------------------------------------ dark theme and phone
if (want("dark")) {
  const d = await ctxFor("student", { dark: true });
  await visit(d, "d_dash", "/app"); await visit(d, "d_genome", "/app/genome"); await visit(d, "d_trace", "/app/roots?trace=10"); await visit(d, "d_roots", "/app/roots");
  await d.ctx.close();
}
if (want("phone")) {
  const p = await ctxFor("student", { vw: 390, vh: 844, dpr: 3, mobile: true });
  const sessions = await api(p.token, "/sessions");
  for (const [n, path] of [["p_dash", "/app"], ["p_roots", "/app/roots"], ["p_genome", "/app/genome"], ["p_session", `/app/library/${sessions?.[0]?.id}`], ["p_flash", "/app/flashcards"]]) {
    const page = await p.ctx.newPage();
    await page.goto(BASE + path); await settle(page, 1800);
    await page.screenshot({ path: `shots/${n}.png` });
    meta[n] = { w: 390, h: 844, tallH: 844, region: null }; save();
    console.log(n);
    await page.close();
  }
  await p.ctx.close();
}
await browser.close();
