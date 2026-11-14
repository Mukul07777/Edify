"""Root-cause gap tracing: why a topic doesn't make sense, found by going back through the chapters it rests on.

A student who can't follow torque is rarely missing torque. They are missing the cross product (Class 11 vectors),
which rests on angles and components (Class 10 trigonometry), which rests on similar triangles (Class 9). Coaching
re-teaches the symptom; this finds the cause:

1. Trace. A model picks the chain of prerequisite chapters for the topic, from real chapters of the syllabus and
   the earlier school classes only (never invented ones), closest first, each with the exact idea it supplies and
   one quick question that checks it. The chain is the same for every student, so it is stored once (PrereqMap)
   and only the first student to trace a chapter spends any AI.
2. Diagnose. The student answers the questions. The deepest link they miss is the root gap: fix that and the links
   above it can hold.
3. Fix. A five-minute lesson on the root idea, in the student's language, ending with how it unlocks the topic they
   were stuck on, and a fresh question to show the gap is closed.

Open roots go to the student's Edify Coach, which then plans the root before the symptom.
"""
from __future__ import annotations

import logging
import random
from functools import cache
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models._util import utcnow
from app.models.gap import GapTrace, PrereqMap
from app.models.user import User
from app.models.weak import WeakTopic
from app.services import ai, syllabus
from app.services.llm import LLMUnavailable, llm
from app.services.syllabus import Chapter, Syllabus

log = logging.getLogger("edify.gaps")

MAX_LINKS = 4
POOL_LIMIT = 220
# the school subjects a subject's ideas come from (languages and humanities never feed a science chain)
FAMILY = {
    "Physics": ("Physics", "Mathematics", "Science"),
    "Chemistry": ("Chemistry", "Science", "Mathematics"),
    "Biology": ("Biology", "Science", "Chemistry"),
    "Botany": ("Biology", "Science", "Chemistry"),
    "Zoology": ("Biology", "Science", "Chemistry"),
    "Mathematics": ("Mathematics",),
    "Science": ("Science", "Mathematics"),
}


class GapError(Exception):
    """Something the student should be told plainly (no chain could be found, a step out of order)."""


# ---------------------------------------------------------------------------------------------------- chapters
@cache
def _school_by_id() -> dict[str, Chapter]:
    return {c.id: c for _, c in syllabus._school_chapters().values()}


def chapter(syl: Syllabus | None, chapter_id: str) -> Chapter | None:
    return (syl.by_id.get(chapter_id) if syl else None) or _school_by_id().get(chapter_id)


def _level(ch: Chapter, syl: Syllabus | None) -> int:
    """How far along a student meets this chapter, as a school class (college and GATE come after Class 12)."""
    if syl is not None and syl.kind in ("college", "gate", "placement"):
        return 13
    return ch.cls if 1 <= ch.cls <= 12 else 11


def candidates(syl: Syllabus | None, target: Chapter) -> list[Chapter]:
    """The chapters a chain may use: what comes before the target in the student's own syllabus, and the related
    subjects of the school classes before it."""
    level = _level(target, syl)
    family = FAMILY.get(target.subject, (target.subject, "Mathematics"))
    pool: list[Chapter] = []
    if syl is not None and target.id in syl.by_id:
        same = syl.subject_chapters(target.subject)
        pool += same[max(0, same.index(target) - 14):same.index(target)]
        if target.subject != "Mathematics" and syl.has_subject("Mathematics"):
            pool += [c for c in syl.subject_chapters("Mathematics") if c.cls <= target.cls]
    top = min(level, 11 if level >= 11 else level)  # an entrance syllabus covers Classes 11-12 itself
    for c in _school_by_id().values():
        if c.subject in family and max(5, level - 5) <= c.cls < max(top, 6) and c.id != target.id:
            pool.append(c)
    seen: set[str] = set()
    out = [c for c in pool if c.id != target.id and not (c.id in seen or seen.add(c.id))]
    return out[-POOL_LIMIT:]


# ---------------------------------------------------------------------------------------------------- the chain
TRACE_SYSTEM = """You find why a student can't follow a topic: the earlier ideas it rests on, the way a great teacher
diagnoses a weak student. Think about what a student must ALREADY know before this topic can make sense.

Choose a chain of 2 to {most} prerequisite chapters, ONLY from the CANDIDATES (copy each id exactly):
- Every link must be a genuine prerequisite: an idea TAUGHT IN THAT CANDIDATE CHAPTER (not an idea of the topic
  itself, and not one the chapter doesn't teach). Torque, for instance, is not a prerequisite of rotational motion.
- Order: link 1 is what the topic uses most directly; each next link is what the previous one rests on, going
  DOWN to earlier classes (the class never goes up along the chain).
- At least one link must come from Class 10 or earlier: that is where most real gaps start (algebra, ratios,
  trigonometry, graphs, basic science).
For each link give:
- chapter_id
- idea: the exact concept from that chapter the topic needs (3 to 8 words)
- why: one line on how the topic (or the link above) uses it
- check: one multiple-choice question testing exactly that idea, answerable in under a minute without a calculator:
  {{"q": the question, "options": 4 short options, "answer": index 0-3 of the right one, "explain": one line}}
Return {{"chain": [...]}}. Use $...$ for maths."""


def _clean_check(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    options = [str(o).strip() for o in raw.get("options") or [] if str(o).strip()]
    try:
        answer = int(raw.get("answer"))
    except (TypeError, ValueError):
        return None
    q = str(raw.get("q") or raw.get("question") or "").strip()
    if not q or len(options) != 4 or not 0 <= answer < 4:
        return None
    return {"q": q, "options": options, "answer": answer, "explain": str(raw.get("explain") or "").strip()}


def _ask_chain(syl: Syllabus | None, target: Chapter, topic_name: str | None) -> list[dict[str, Any]]:
    pool = candidates(syl, target)
    if not pool:
        raise GapError("There are no earlier chapters to trace this one back to.")
    by_id = {c.id: c for c in pool}
    listing = "\n".join(f"{c.id} | Class {c.cls if 1 <= c.cls <= 12 else '11-12'} | {c.subject} | {c.name}" for c in pool)
    what = f"{target.subject}: {target.name}" + (f" (the topic: {topic_name})" if topic_name else "")
    data = llm.json([{"role": "system", "content": TRACE_SYSTEM.format(most=MAX_LINKS)},
                     {"role": "user", "content": f"TOPIC: {what}\n\nCANDIDATES (id | class | subject | chapter):\n{listing}"}],
                    max_tokens=4000, temperature=0.1, effort="medium", feature="gap_trace")  # shared by every student: worth thinking
    chain: list[dict[str, Any]] = []
    for link in data.get("chain") or []:
        if not isinstance(link, dict):
            continue
        ch = by_id.get(str(link.get("chapter_id") or "").strip())
        check = _clean_check(link.get("check"))
        if ch is None or check is None or any(x["chapter_id"] == ch.id for x in chain):
            continue  # an invented chapter, a broken question or a repeat: dropped, never shown
        if chain and chain[-1]["cls"] and 1 <= ch.cls <= 12 and ch.cls > chain[-1]["cls"]:
            continue  # the chain only goes down to earlier classes
        chain.append({"chapter_id": ch.id, "name": ch.name, "subject": ch.subject, "cls": ch.cls if 1 <= ch.cls <= 12 else None,
                      "idea": str(link.get("idea") or ch.name).strip()[:120], "why": str(link.get("why") or "").strip()[:240],
                      "check": check})
    if not chain:
        raise GapError("Couldn't work out what this topic rests on right now. Try again in a minute.")
    return chain[:MAX_LINKS]


def prereq_chain(db: Session, syl: Syllabus | None, target: Chapter, topic_id: str | None, topic_name: str | None) -> tuple[list, bool]:
    """The chain for a chapter (or one of its topics), and whether the AI had to be asked (False: shared, free)."""
    key = f"{target.id}#{topic_id}" if topic_id else target.id
    hit = db.get(PrereqMap, key)
    if hit and hit.chain:
        return hit.chain, False
    chain = _ask_chain(syl, target, topic_name)
    db.merge(PrereqMap(key=key, chain=chain))
    db.commit()
    return chain, True


# ---------------------------------------------------------------------------------------------------- a trace
def start(db: Session, user: User, syl: Syllabus | None, chapter_id: str, topic_id: str | None) -> tuple[GapTrace, bool]:
    target = chapter(syl, chapter_id)
    if target is None:
        raise GapError("That chapter isn't in your syllabus.")
    topic = next((t for t in target.topics if t.id == topic_id), None) if topic_id else None
    chain, used_ai = prereq_chain(db, syl, target, topic.id if topic else None, topic.name if topic else None)
    trace = GapTrace(user_id=user.id, chapter_id=target.id, topic_id=topic.id if topic else None,
                     title=f"{topic.name} ({target.name})" if topic else target.name,
                     chain=[{**link, "result": None} for link in chain], status="checking")
    db.add(trace)
    db.commit()
    return trace, used_ai


def owned(db: Session, user: User, trace_id: int) -> GapTrace:
    trace = db.get(GapTrace, trace_id)
    if trace is None or trace.user_id != user.id:
        raise GapError("That trace doesn't exist.")
    return trace


def answer(db: Session, trace: GapTrace, choices: list[int | None]) -> GapTrace:
    """Mark each link; the root gap is the deepest link missed (fix the bottom and the ones above it can hold)."""
    if trace.status != "checking":
        raise GapError("These questions are already answered.")
    chain = [dict(link) for link in trace.chain or []]
    if len(choices) != len(chain):
        raise GapError("Answer every question (or skip it) first.")
    for link, choice in zip(chain, choices):
        link["choice"] = choice
        link["result"] = "right" if choice == link["check"]["answer"] else "wrong"  # a skip counts as not known yet
    missed = [i for i, link in enumerate(chain) if link["result"] == "wrong"]
    trace.chain = chain
    trace.root = missed[-1] if missed else None
    trace.status = "found" if missed else "clear"
    db.commit()
    return trace


LESSON_SYSTEM = """You fix one gap in a student's foundations in five minutes. The student is stuck on "{target}"
because they don't yet have this earlier idea: "{idea}" (from {chapter}, {where}).

Write the fix in Markdown, under 220 words:
1. The idea in plain words, the way a good senior would explain it.
2. An everyday example from Indian life.
3. One short worked example.
4. A last line starting "How this unlocks {target}:" that connects it to what they were stuck on.
Use $...$ for maths. Then one NEW multiple-choice question (different from: "{old_q}") that shows the gap is closed.
Return {{"lesson_md": "...", "check": {{"q", "options": 4, "answer": 0-3, "explain"}}}}."""


def lesson(db: Session, user: User, trace: GapTrace) -> tuple[GapTrace, bool]:
    """The short lesson for the root gap, shared between students who share the gap and the language."""
    if trace.status not in ("found", "fixed") or trace.root is None:
        raise GapError("There's no root gap to fix on this trace.")
    if trace.lesson:
        return trace, False
    link = trace.chain[trace.root]
    key = f"lesson:{link['chapter_id']}:{link['idea'][:80]}:{trace.chapter_id}:{user.language or 'en'}"
    hit = db.get(PrereqMap, key)
    used_ai = False
    if hit and hit.chain:
        made = hit.chain
    else:
        target = trace.title
        where = f"Class {link['cls']}" if link.get("cls") else "earlier in your course"
        data = llm.json([{"role": "system", "content": ai._in(LESSON_SYSTEM.format(
                            target=target, idea=link["idea"], chapter=link["name"], where=where, old_q=link["check"]["q"]), user.language)},
                         {"role": "user", "content": f"Why the topic needs it: {link.get('why') or link['idea']}"}],
                        max_tokens=2200, temperature=0.3, feature="gap_lesson")
        check = _clean_check(data.get("check"))
        md = str(data.get("lesson_md") or "").strip()
        if not md or check is None:
            raise GapError("Couldn't write the lesson right now. Try again in a minute.")
        made = {"md": ai.fix_latex(md), "check": check}
        db.merge(PrereqMap(key=key, chain=made))
        used_ai = True
    trace.lesson = {**made, "result": None}
    db.commit()
    return trace, used_ai


def recheck(db: Session, trace: GapTrace, choice: int) -> GapTrace:
    if not trace.lesson:
        raise GapError("Read the lesson first.")
    right = choice == trace.lesson["check"]["answer"]
    trace.lesson = {**trace.lesson, "choice": choice, "result": "right" if right else "wrong"}
    if right:
        trace.status = "fixed"
    db.commit()
    return trace


# ---------------------------------------------------------------------------------------------------- what's shown
def view(trace: GapTrace) -> dict[str, Any]:
    """A trace for the app. While the questions are open, their answers stay on the server."""
    answered = trace.status != "checking"
    chain = []
    for link in trace.chain or []:
        check = link["check"] if answered else {"q": link["check"]["q"], "options": link["check"]["options"]}
        chain.append({**{k: v for k, v in link.items() if k != "check"}, "check": check})
    lesson_out = None
    if trace.lesson:
        done = trace.lesson.get("result") is not None
        c = trace.lesson["check"]
        lesson_out = {"md": trace.lesson["md"], "result": trace.lesson.get("result"), "choice": trace.lesson.get("choice"),
                      "check": c if done else {"q": c["q"], "options": c["options"]}}
    return {"id": trace.id, "title": trace.title, "chapter_id": trace.chapter_id, "topic_id": trace.topic_id,
            "status": trace.status, "root": trace.root, "chain": chain, "lesson": lesson_out,
            "created_at": trace.created_at.isoformat() + "Z" if trace.created_at else None}


def overview(db: Session, user: User, syl: Syllabus | None) -> dict[str, Any]:
    traces = db.scalars(select(GapTrace).where(GapTrace.user_id == user.id).order_by(GapTrace.id.desc()).limit(12)).all()
    weak = db.scalars(select(WeakTopic).where(WeakTopic.user_id == user.id, WeakTopic.status == "open")
                      .order_by(WeakTopic.misses.desc()).limit(10)).all()
    suggestions = []
    for w in weak:
        ch = chapter(syl, w.chapter_id)
        if ch is None:
            continue
        topic = next((t for t in ch.topics if t.id == w.topic_id), None)
        suggestions.append({"chapter_id": ch.id, "topic_id": topic.id if topic else None, "subject": ch.subject,
                            "name": topic.name if topic else ch.name, "chapter": ch.name, "misses": w.misses})
    chapters = [{"id": c.id, "subject": c.subject, "name": c.name, "cls": c.cls} for c in (syl.chapters if syl else ())]
    return {"traces": [view(t) for t in traces], "suggestions": suggestions, "chapters": chapters,
            "fixed": sum(t.status == "fixed" for t in traces)}


def open_roots(db: Session, user_id: int) -> list[dict[str, Any]]:
    """Root gaps found and not yet fixed, for the coach to plan around."""
    rows = db.scalars(select(GapTrace).where(GapTrace.user_id == user_id, GapTrace.status == "found")
                      .order_by(GapTrace.id.desc()).limit(6)).all()
    out = []
    for t in rows:
        if t.root is None or not t.chain:
            continue
        link = t.chain[t.root]
        out.append({"stuck_on": t.title, "root": link["idea"], "chapter": link["name"], "cls": link.get("cls"), "trace_id": t.id})
    return out


def shuffle_seed(trace: GapTrace) -> int:  # kept for a later option order per student; the order is fixed for now
    return random.Random(trace.id).randint(0, 3)


__all__ = ["GapError", "LLMUnavailable", "answer", "candidates", "chapter", "lesson", "open_roots", "overview", "owned",
           "prereq_chain", "recheck", "start", "utcnow", "view"]
