"""The next-class kit: what a teacher should do about the board that lost the room.

The confusion map shows *where* a lecture lost students. This turns one board's evidence (the wrong options they
picked, the doubts they asked, how many tapped "I'm lost") into what to do about it next class: the misconception
the wrong answers point to, a simpler way to explain it, an everyday analogy, what to write on the board, two
questions to open the class with, and the earlier-class idea the room is probably missing (the same root-cause
idea as a student's gap trace, applied to a whole class). Kept per board until new evidence comes in.
"""
from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.gap import PrereqMap
from app.models.note import Note
from app.models.room import LectureSignal
from app.services import ai
from app.services.gaps import _clean_check
from app.services.llm import llm

LEAD = re.compile(r"^\s*(?:\d+\s*[.)]|\d️?⃣|[-*•])\s*")

SYSTEM = """You help a teacher fix the part of a lecture that lost the class, in the next class.

You get one board from the lecture and the evidence: wrong answers to a quiz on it (with which wrong options
students chose), the doubts students asked, and how many tapped "I'm lost". Diagnose, then plan. The strongest
evidence is the WRONG OPTION MOST STUDENTS PICKED: the misconception is the idea that makes that option look right
(compare it with the right one). The doubts confirm it. Be concrete and classroom-ready for an Indian classroom.
Use $...$ for maths.
Return {{
 "misconception": the most likely wrong idea in students' heads, read from the evidence (1-2 sentences),
 "simpler": a simpler re-explanation the teacher can say in two minutes (Markdown, under 130 words),
 "analogy": one everyday Indian analogy that makes it click (1-2 sentences),
 "board_plan": 3 or 4 short lines to write on the board, in order,
 "openers": 2 multiple-choice questions to open the next class, each {{"q", "options": 4, "answer": 0-3, "explain"}},
 "root_idea": the earlier-class idea the class is probably missing (3-8 words), and "root_class": the school class
 (CBSE, 5 to 12) where that idea is first taught, or null if unsure
}}"""


def evidence(db: Session, code: str, note_id: int) -> dict[str, Any] | None:
    note = db.get(Note, note_id)
    if note is None:
        return None
    signals = db.scalars(select(LectureSignal).where(LectureSignal.room_code == code, LectureSignal.note_id == note_id)).all()
    quizzes, doubts, lost, wrong = [], [], 0, 0
    for s in signals:
        if s.kind == "lost":
            lost += 1
        elif s.kind == "wrong":
            wrong += 1
        elif s.kind == "doubt" and s.text:
            doubts.append(s.text[:300])
        elif s.kind == "quiz" and s.data:
            d = s.data
            options, counts, answer = d.get("options") or [], d.get("counts") or [], d.get("answer_index")
            right = options[answer] if isinstance(answer, int) and answer < len(options) else None
            wrong_picks = sorted(((c, o) for o, c in zip(options, counts) if c and o != right), reverse=True)
            quizzes.append({"question": (s.text or "")[:300], "right_option": right, "picked": {o: c for o, c in zip(options, counts) if c},
                            "most_picked_wrong": wrong_picks[0][1] if wrong_picks else None})
    board = (note.ai_notes or note.ocr_raw or "")[:2500]
    return {"topic": note.topic or "this board", "board": board, "lost": lost, "wrong": wrong, "doubts": doubts[:10], "quizzes": quizzes[:4]}


def kit(db: Session, code: str, note_id: int, language: str | None) -> tuple[dict[str, Any] | None, bool]:
    """The kit for one board, and whether the AI had to be asked (False: the evidence hasn't changed since)."""
    ev = evidence(db, code, note_id)
    if ev is None:
        return None, False
    key = f"reteach:{code}:{note_id}:{ev['lost']}:{ev['wrong']}:{len(ev['doubts'])}:{language or 'en'}"
    hit = db.get(PrereqMap, key)
    if hit and hit.chain:
        return hit.chain, False
    data = llm.json([{"role": "system", "content": ai._in(SYSTEM, language)},
                     {"role": "user", "content": f"Board topic: {ev['topic']}\n\nBoard:\n{ev['board']}\n\n"
                                                 f"Tapped 'I'm lost': {ev['lost']}. Wrong quiz answers: {ev['wrong']}.\n"
                                                 f"Quizzes (which options were picked, and how often): {ev['quizzes']}\n"
                                                 f"Doubts asked: {ev['doubts']}"}],
                    max_tokens=2600, temperature=0.3, feature="reteach_kit")
    openers = [c for c in (_clean_check(q) for q in data.get("openers") or []) if c][:2]
    # the list is numbered on screen: a model's own "1." or "1️⃣" in front of a line goes
    plan = [LEAD.sub("", str(x)).strip() for x in data.get("board_plan") or [] if LEAD.sub("", str(x)).strip()][:4]
    try:
        root_class = int(data.get("root_class")) if data.get("root_class") not in (None, "") else None
    except (TypeError, ValueError):
        root_class = None
    made = {"topic": ev["topic"], "evidence": {"lost": ev["lost"], "wrong": ev["wrong"], "doubts": len(ev["doubts"])},
            "misconception": str(data.get("misconception") or "").strip(), "simpler": ai.fix_latex(str(data.get("simpler") or "").strip()),
            "analogy": str(data.get("analogy") or "").strip(), "board_plan": plan, "openers": openers,
            "root_idea": str(data.get("root_idea") or "").strip(), "root_class": root_class if root_class and 5 <= root_class <= 12 else None}  # "Class 3" for sin 2θ: dropped
    if not made["simpler"] or not made["misconception"]:
        return None, True
    db.merge(PrereqMap(key=key, chain=made))
    db.commit()
    return made, True
