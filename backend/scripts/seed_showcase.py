"""One demo account for the judges with every root-cause feature ready, and the Gap Genome filled in. No AI needed.

    python scripts/seed_showcase.py [--password ...]

Run it again any time: it deletes its own accounts and makes them fresh. What it makes, through the app's real
endpoints where a student would have clicked:

  - the Gap Genome: hand-checked prerequisite chains for 32 JEE / NEET chapters (scripts/genome_data.py), stored
    exactly where the AI would store them, with five-minute English lessons for the ideas the demo can land on
  - a demo cohort of 24 JEE students with traces through those chains, so the Genome's rings and "where trouble
    really starts" have weights (a demo account sees only this cohort; real accounts never see it)
  - the judge's account (English, Class 12, JEE Main):
      My plan and Prep Hub: a goal, Class 11 mostly done, a few topics ticked today, chapters revised
      Weak spots: two mock tests; Physics lost marks in three chapters that all rest on Class 10 Electricity
      Root cause: "Edify noticed" (Class 10 Electricity, then Class 8 powers of ten), one trace FIXED
      (Rotational Motion: root Class 10 trigonometry, 1 of 3 before, 3 of 3 after), one root still open
  - a teacher with the cohort and the judge in one batch: "where your batch's gaps start" and a ready recap
"""
from __future__ import annotations

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import genome_data as G  # noqa: E402

DOMAIN = "example.com"
JUDGE = "demo.edify.judge@" + DOMAIN
TEACHER = "demo.edify.batchteacher@" + DOMAIN
COHORT = 24
LANG = "en"

# the stuck chapters the cohort traced, and how often (electricity and mechanics are where JEE students struggle most)
COHORT_TARGETS = {
    "physics.current-electricity": 6, "physics.electrostatics": 5, "physics.magnetic-effects-of-current-and-magnetism": 4,
    "physics.rotational-motion": 5, "physics.kinematics": 3, "physics.laws-of-motion": 3, "physics.electromagnetic-induction-and-ac": 2,
    "physics.oscillations-and-waves": 2, "physics.gravitation": 2, "physics.work-energy-and-power": 2,
    "chemistry.chemical-kinetics": 2, "chemistry.redox-reactions-and-electrochemistry": 2, "chemistry.chemical-bonding-and-molecular-structure": 2,
    "chemistry.some-basic-concepts-of-chemistry": 2, "chemistry.atomic-structure": 1, "chemistry.solutions": 1,
    "mathematics.integral-calculus": 1, "mathematics.limits-continuity-and-differentiability": 1,
}
DEEP = {"elec10": 3.0, "trig10": 3.0, "power8": 1.6, "mole9": 1.6}  # the load-bearing ideas, where real gaps cluster


def names() -> dict[str, tuple[str, str, int | None]]:
    from app.services import gaps
    out = {c.id: (c.name, c.subject, c.cls if 1 <= c.cls <= 12 else None) for c in gaps._school_by_id().values()}
    out.update({c.id: (c.name, c.subject, c.cls) for c in gaps._exam_by_id().values()})
    return out


LESSON_BY_CHAPTER = {link["chapter_id"]: alias for alias, link in G.LINKS.items() if link.get("lesson")}
LESSON_BY_CHAPTER.update({"mathematics.trigonometry": "trig10",  # the same idea, met again in Class 11
                          "c10.mathematics.pair-of-linear-equations-in-two-variables": "linpoly9"})


def lesson_key(link: dict, target: str) -> str:
    return f"lesson:{link['chapter_id']}:{link['idea'][:80]}:{target}:{LANG}"


def load_genome(db) -> tuple[int, int, int]:
    """Chains for the chapters that have none yet (a chain the AI already built is kept: it is real data), and the
    English lessons for every stored link they fit, written where gaps.prereq_chain and gaps._made_lesson look first."""
    from sqlalchemy import select
    from app.models.gap import PrereqMap
    nm = names()
    added = 0
    for target in G.CHAINS:
        hit = db.get(PrereqMap, target)
        if not (hit and hit.chain):
            db.merge(PrereqMap(key=target, chain=G.chain(target, nm)))
            added += 1
    db.flush()
    lessons = 0
    for target, chain in db.execute(select(PrereqMap.key, PrereqMap.chain).where(~PrereqMap.key.like("lesson:%"))).all():
        if "#" in target or not chain or target not in nm:
            continue
        for link in chain:
            alias = LESSON_BY_CHAPTER.get(link["chapter_id"])
            key = lesson_key(link, target)
            if alias and not db.get(PrereqMap, key):
                db.add(PrereqMap(key=key, chain={"md": G.lesson_md(alias, nm[target][0], link.get("why") or link["idea"]),
                                                 "check": G.LINKS[alias]["fix"]}))
                lessons += 1
    db.commit()
    total = db.scalar(select(PrereqMap.key).where(~PrereqMap.key.like("lesson:%")).limit(1)) and len(
        [k for k in db.scalars(select(PrereqMap.key).where(~PrereqMap.key.like("lesson:%"))) if "#" not in k])
    return added, lessons, total or 0


def wipe(db) -> None:
    from sqlalchemy import select
    from app.models.user import User
    from app.services import account
    mine = [JUDGE, TEACHER] + [f"demo.edify.cohort{i:02}@{DOMAIN}" for i in range(1, COHORT + 1)]
    mine += [e.replace("demo.edify.", "demo.focs.") for e in mine]  # the same accounts made before the rename
    for user in db.scalars(select(User).where(User.email.in_(mine))).all():
        account.delete_everything(db, user)
    db.commit()


def register(client, email: str, name: str, password: str, language: str | None = None) -> dict:
    from app.core import ratelimit
    ratelimit.reset()
    r = client.post("/api/auth/register", json={"full_name": name, "email": email, "password": password, "accepted_terms": True,
                                                "exam_target": "jee", "class_level": "Class 12"})
    r.raise_for_status()
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    if language:
        client.patch("/api/auth/me", headers=h, json={"language": language}).raise_for_status()
    return h


def answers_for(chain: list[dict], root: int | None) -> list[int]:
    """Choices that land the trace on ``root``: that link wrong, every deeper one right (the root is the deepest miss)."""
    return [(c["check"]["answer"] + 1) % 4 if i == root else c["check"]["answer"] for i, c in enumerate(chain)]


ROTATION_RETEST = {  # the stuck topic itself, before the trace and after the fix (the bank had five, the trace needs six)
    "before": {"items": [
        G.q("A force of 10 N acts at the end of a 0.5 m spanner, perpendicular to it. The torque is…", ["2 N m", "5 N m", "10 N m", "20 N m"], 1, "τ = rF = 0.5 × 10 = 5 N m"),
        G.q("The same 10 N force on the 0.5 m spanner acts at 30° to it. The torque is…", ["2.5 N m", "4.3 N m", "5 N m", "10 N m"], 0, "τ = rF sin 30° = 2.5 N m"),
        G.q("A torque of 6 N m turns a wheel with I = 2 kg m². Its angular acceleration is…", ["3 rad/s²", "4 rad/s²", "8 rad/s²", "12 rad/s²"], 0, "α = τ/I = 3"),
    ], "choices": None, "right": None},
    "after": {"items": [
        G.q("A 20 N force acts 0.2 m from a hinge at 90°. The torque is…", ["2 N m", "4 N m", "10 N m", "100 N m"], 1, "τ = 0.2 × 20 = 4 N m"),
        G.q("A force pushes a door straight towards its hinge (θ = 0°). The torque is…", ["Maximum", "Half", "Zero", "Negative"], 2, "sin 0° = 0"),
        G.q("A 12 N m torque acts on a disc with I = 3 kg m². Its angular acceleration is…", ["3 rad/s²", "4 rad/s²", "9 rad/s²", "36 rad/s²"], 1, "α = 12/3 = 4"),
    ], "choices": None, "right": None},
}


def db_root(trace_id: int) -> str:
    from app.core.database import SessionLocal
    from app.models.gap import GapTrace
    with SessionLocal() as db:
        t = db.get(GapTrace, trace_id)
        return t.chain[t.root]["name"] if t and t.root is not None else "none"


def seed(client, password: str) -> dict:
    from sqlalchemy import select
    from app.core import ratelimit
    from app.core.database import SessionLocal
    from app.models._util import utcnow
    from app.models.gap import GapTrace, PrereqMap
    from app.models.user import User
    from app.services import gaps, syllabus, weak

    with SessionLocal() as db:
        wipe(db)
        added, lessons, total = load_genome(db)
    print(f"Gap Genome: {total} chains ({added} added by hand, the rest kept as the AI built them), {lessons} English lessons added")

    # ---------------------------------------------------------------- the teacher and the batch
    th = register(client, TEACHER, "Demo Teacher (Physics)", password, LANG)
    ratelimit.reset()
    batch = client.post("/api/classes", headers=th, json={"name": "Demo: JEE 2027 Physics batch"})
    batch.raise_for_status()
    batch = batch.json()

    # ---------------------------------------------------------------- the demo cohort
    nm = names()
    rng = random.Random(2027)
    targets, weights = list(COHORT_TARGETS), list(COHORT_TARGETS.values())
    made = fixed = 0
    for i in range(1, COHORT + 1):
        h = register(client, f"demo.edify.cohort{i:02}@{DOMAIN}", f"Demo Cohort {i:02}", password, LANG)
        ratelimit.reset()
        client.post("/api/classes/join", headers=h, json={"code": batch["code"]}).raise_for_status()
        with SessionLocal() as db:
            uid = db.scalar(select(User.id).where(User.email == f"demo.edify.cohort{i:02}@{DOMAIN}"))
            db.get(User, uid).plan = "pro"
            for target in {rng.choices(targets, weights)[0] for _ in range(rng.choice((1, 2, 2, 3)))}:
                chain = db.get(PrereqMap, target).chain
                aliases = [LESSON_BY_CHAPTER.get(c["chapter_id"], "") for c in chain]
                options = [k for k, a in enumerate(aliases) if a]  # roots a lesson is ready for (the batch recap needs one)
                if not options:
                    continue
                root = rng.choices(options, [DEEP.get(aliases[k], 1.0) for k in options])[0]
                picks = answers_for(chain, root)
                linked = [{**c, "choice": p, "result": "right" if p == c["check"]["answer"] else "wrong"} for c, p in zip(chain, picks)]
                is_fixed = rng.random() < 0.55
                lesson = None
                if is_fixed:
                    hit = db.get(PrereqMap, lesson_key(chain[root], target))
                    lesson = {**hit.chain, "result": "right"} if hit else None
                when = utcnow() - timedelta(days=rng.randint(1, 20), hours=rng.randint(0, 23))
                db.add(GapTrace(user_id=uid, chapter_id=target, title=nm[target][0],
                                chain=linked, root=root, lesson=lesson, status="fixed" if lesson else "found",
                                created_at=when, updated_at=when))
                made += 1
                fixed += bool(lesson)
            db.commit()
    print(f"Demo cohort: {COHORT} students, {made} traces, {fixed} fixed")

    # ---------------------------------------------------------------- the judge
    h = register(client, JUDGE, "Demo Aarav (JEE 2027)", password, LANG)
    with SessionLocal() as db:
        db.scalar(select(User).where(User.email == JUDGE)).plan = "pro"
        db.commit()
    ratelimit.reset()
    client.post("/api/classes/join", headers=h, json={"code": batch["code"]}).raise_for_status()

    # My plan and Prep Hub: JEE Main in January, Class 11 mostly covered, Class 12 under way
    today = date.today()
    exam_day = date(today.year + 1, 1, 22) if today.month >= 3 else date(today.year, 1, 22)
    goal = {"track": "jee_main", "class_level": "12", "exam_date": exam_day.isoformat(), "target": "air_10k",
            "dream": "IIT Bombay, Computer Science", "weekday_hours": 6, "weekend_hours": 9, "coaching": "offline",
            "standing": {"Physics": {"11": "done", "12": "partial"}, "Chemistry": {"11": "partial", "12": "partial"},
                         "Mathematics": {"11": "done", "12": "partial"}},
            "apply_standing": True}
    client.put("/api/prep/goal", headers=h, json=goal).raise_for_status()
    syl = syllabus.get("jee")
    ticked = 0
    for cid in ("physics.current-electricity", "chemistry.equilibrium", "mathematics.integral-calculus"):
        for t in syl.by_id[cid].topics[:2]:
            ticked += client.put(f"/api/prep/topics/{t.id}", headers=h, json={"done": True}).status_code == 200
    for cid in ("physics.kinematics", "physics.laws-of-motion", "mathematics.trigonometry"):
        client.put(f"/api/prep/chapters/{cid}/revision", headers=h, json={"done": True})
    print(f"Judge: plan to JEE Main {exam_day}, {ticked} topics ticked today, 3 chapters revised")

    # Weak spots: two mocks. Physics lost marks in three chapters that all rest on Class 10 Electricity.
    with SessionLocal() as db:
        uid = db.scalar(select(User.id).where(User.email == JUDGE))
        weak.save_test(db, uid, syl, title="[Demo] Minor Test 3 (Physics)", taken_on=today - timedelta(days=2), score=118, max_score=300,
                       subjects=[{"name": "Physics", "score": 22, "max": 100}, {"name": "Chemistry", "score": 46, "max": 100},
                                 {"name": "Mathematics", "score": 50, "max": 100}], source="manual",
                       weak=[{"chapter_id": "physics.current-electricity", "misses": 4, "note": "Kirchhoff loops and power"},
                             {"chapter_id": "physics.electrostatics", "misses": 3, "note": "Potential and capacitors"},
                             {"chapter_id": "physics.magnetic-effects-of-current-and-magnetism", "misses": 2, "note": "Field of a current loop"}])
        weak.save_test(db, uid, syl, title="[Demo] Part Test 2 (Chemistry + Maths)", taken_on=today - timedelta(days=9), score=141, max_score=300,
                       subjects=[{"name": "Chemistry", "score": 38, "max": 100}, {"name": "Mathematics", "score": 55, "max": 100},
                                 {"name": "Physics", "score": 48, "max": 100}], source="manual",
                       weak=[{"chapter_id": "chemistry.equilibrium", "misses": 1, "note": "pH and buffer calculations"},
                             {"chapter_id": "chemistry.chemical-kinetics", "misses": 2, "note": "Half-life and order"},
                             {"chapter_id": "mathematics.integral-calculus", "misses": 1, "note": "Area between curves"}])
        db.commit()

    # Root cause: Rotational Motion traced and fixed (root: Class 10 trigonometry), Laws of Motion's root still open
    ratelimit.reset()
    rot = client.post("/api/gaps", headers=h, json={"chapter_id": "physics.rotational-motion"})
    rot.raise_for_status()
    rid = rot.json()["id"]
    with SessionLocal() as db:
        t = db.get(GapTrace, rid)
        t.retest = ROTATION_RETEST
        chain = t.chain
        db.commit()
    before = [ROTATION_RETEST["before"]["items"][0]["answer"], 2, 3]  # 1 of 3 before
    trig = next((i for i, c in enumerate(chain) if "trigonometry" in c["chapter_id"]), 0)  # the root: trigonometry
    client.post(f"/api/gaps/{rid}/answers", headers=h, json={"answers": answers_for(chain, trig), "before": before}).raise_for_status()
    ratelimit.reset()
    les = client.post(f"/api/gaps/{rid}/lesson", headers=h)
    les.raise_for_status()
    with SessionLocal() as db:
        right = db.get(GapTrace, rid).lesson["check"]["answer"]
    client.post(f"/api/gaps/{rid}/check", headers=h, json={"choice": right}).raise_for_status()
    after = [item["answer"] for item in ROTATION_RETEST["after"]["items"]]
    client.post(f"/api/gaps/{rid}/after", headers=h, json={"answers": after}).raise_for_status()

    ratelimit.reset()
    lom = client.post("/api/gaps", headers=h, json={"chapter_id": "physics.laws-of-motion"})
    lom.raise_for_status()
    with SessionLocal() as db:
        chain = db.get(GapTrace, lom.json()["id"]).chain
    client.post(f"/api/gaps/{lom.json()['id']}/answers", headers=h, json={"answers": answers_for(chain, 0)}).raise_for_status()

    with SessionLocal() as db:
        sus = gaps.suspects(db, uid, syl)
        view = gaps.genome(db, demo=True)
    print(f"Judge: Rotational Motion fixed (root: {db_root(rid)},1/3 -> 3/3), Laws of Motion root open")
    for s in sus:
        print(f"  Edify noticed: {', '.join(s['because'])} all rest on Class {s['cls']} {s['name']}")
    top = view["top"][0]
    print(f"Genome (demo view): {view['exam_chapters']} exam chapters, {view['foundations']} foundations, {view['links']} links, "
          f"{view['students']} students, {view['rooted']} roots; load-bearing: {top['name']} under {top['underpins']} chapters")
    return {"judge": JUDGE, "teacher": TEACHER, "class": batch}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--password", default="EdifyDemo@2026")
    args = ap.parse_args()
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        out = seed(client, args.password)
    print(f"\nReady. Password for every account: {args.password}")
    print(f"  judge   {out['judge']}")
    print(f"  teacher {out['teacher']}  (batch: /app/classes/{out['class']['id']})")


if __name__ == "__main__":
    main()
