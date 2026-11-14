"""Edify Coach: each student's own study coach, an agent on its own Maritime machine (agents/edify-coach).

Edify keeps the facts (lectures, weak spots, mock tests); the coach keeps the judgment: it remembers the student
across weeks, writes a revision pack after each lecture, re-plans every night on a Maritime schedule (which wakes it
even while it sleeps), and answers questions with all of it in mind. Edify talks to it through Maritime's REST API:

* PUT  /api/v1/end-users/{id}          the student, as a Maritime end user (``edify_<user id>``)
* POST /api/v1/end-users/{id}/agents   their coach, built from MARITIME_COACH_REPO, created exactly once
* POST /api/agents/{agent}/triggers    the nightly review (also declared by the coach's GET /schedules)
* POST /api/agents/{agent}/chat        every event; a sleeping coach wakes for it

With MARITIME_COACH_URL set instead, the same events go straight to a coach running on this PC (for trying it out).
The last state the coach sent back is kept on the CoachAgent row, so the dashboard never waits on a sleeping coach.
"""
from __future__ import annotations

import json
import logging
import re
import threading
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models._util import utcnow
from app.models.coach import CoachAgent
from app.models.mock import MockTest
from app.models.session import StudySession
from app.models.user import User
from app.models.weak import WeakTopic

log = logging.getLogger("edify.coach")
CHAT_TIMEOUT = 45.0  # a coach answers within Maritime's 30 s, plus waking from sleep


class CoachError(Exception):
    """The coach could not be reached or set up; the message is fit to show the student."""


def mode() -> str | None:
    if settings.MARITIME_API_KEY and settings.MARITIME_COACH_REPO:
        return "maritime"
    if settings.MARITIME_COACH_URL:
        return "local"
    return None


def end_user_id(user: User) -> str:
    return f"edify_{user.id}"


# ---------------------------------------------------------------------------------------------------- Maritime
def _maritime(method: str, path: str, body: dict[str, Any] | None = None, timeout: float = 30.0) -> Any:
    try:
        r = httpx.request(method, settings.MARITIME_API_URL.rstrip("/") + path, json=body, timeout=timeout,
                          headers={"Authorization": f"Bearer {settings.MARITIME_API_KEY}", "User-Agent": "edify-server"})
    except httpx.HTTPError as exc:
        raise CoachError("Maritime can't be reached right now. Try again in a minute.") from exc
    if r.status_code >= 400:
        log.warning("Maritime %s %s -> %s %s", method, path, r.status_code, r.text[:300])
        raise CoachError(f"Maritime said no ({r.status_code}): {_detail(r)}")
    return r.json() if r.content else {}


def _detail(r: httpx.Response) -> str:
    try:
        body = r.json()
    except ValueError:
        return r.text[:160]
    d = body.get("detail") or body.get("message") or body.get("error") or body
    return (d if isinstance(d, str) else json.dumps(d))[:160]


def _provision(user: User) -> str:
    """The student's coach machine, created once (Maritime answers with the same agent on every later call)."""
    ext = end_user_id(user)
    _maritime("PUT", f"/api/v1/end-users/{ext}", {"displayName": user.full_name, "metadata": {"exam": user.exam_target or ""},
                                                  "tags": ["edify", "coach"]})
    env = [] if settings.MARITIME_USE_LLM or not settings.llm_api_key else [
        {"key": "LLM_API_KEY", "value": settings.llm_api_key, "isSecret": True},
        {"key": "LLM_BASE_URL", "value": settings.LLM_BASE_URL, "isSecret": False},
        {"key": "COACH_MODEL", "value": settings.LLM_MODEL.split(",")[0].strip(), "isSecret": False},
    ]
    agent = _maritime("POST", f"/api/v1/end-users/{ext}/agents", {
        "name": f"edify-coach-{user.id}",
        "description": f"Edify Coach for student {user.id}",
        "framework": "custom",
        "githubRepo": settings.MARITIME_COACH_REPO,
        "branch": settings.MARITIME_COACH_BRANCH,
        "healthCheckPath": "/health",
        "hasWebUi": False,
        "idleTtlSeconds": 600,  # sleeps after 10 quiet minutes; chats and the nightly schedule wake it
        "useMaritimeLlm": settings.MARITIME_USE_LLM,
        "initialEnvVars": env,
    }, timeout=60.0)
    agent_id = str(agent.get("id") or "")
    if not agent_id:
        raise CoachError("Maritime did not return an agent id.")
    try:  # the coach's GET /schedules declares the same review; the platform trigger is the belt to its braces
        _maritime("POST", f"/api/agents/{agent_id}/triggers", {"type": "cron", "config": {
            "cron": settings.COACH_NIGHTLY_CRON, "tz": "Asia/Kolkata", "prompt": json.dumps({"type": "review", "reason": "nightly"})}})
    except CoachError:
        log.info("nightly trigger not added for %s (the coach's own schedule still runs)", agent_id)
    return agent_id


# ---------------------------------------------------------------------------------------------------- talking to it
def _reply(raw: Any) -> dict[str, Any]:
    """The coach answers {"response": "<JSON>"}; Maritime may pass that through whole or as the bare text."""
    for _ in range(3):
        if isinstance(raw, dict):
            if "state" in raw or "error" in raw or "plan" in raw or "answer" in raw or "pack" in raw:
                return raw
            raw = next((raw[k] for k in ("response", "reply", "message", "text", "output") if k in raw), None)
        elif isinstance(raw, str):
            m = re.search(r"\{.*\}", raw, re.S)
            try:
                raw = json.loads(m.group(0)) if m else None
            except ValueError:
                raw = None
        else:
            break
    raise CoachError("The coach sent back something Edify couldn't read.")


def _send(row: CoachAgent, event: dict[str, Any]) -> dict[str, Any]:
    message = json.dumps(event, ensure_ascii=False, default=str)
    if row.mode == "local":
        try:
            r = httpx.post(settings.MARITIME_COACH_URL.rstrip("/") + "/chat", json={"message": message, "source": "edify"}, timeout=CHAT_TIMEOUT)
            r.raise_for_status()
        except httpx.HTTPError as exc:
            raise CoachError("The coach on this computer isn't running (agents/edify-coach/server.py).") from exc
        return _reply(r.json())
    if not row.agent_id:
        raise CoachError("Your coach hasn't been set up yet.")
    try:
        return _reply(_maritime("POST", f"/api/agents/{row.agent_id}/chat", {"message": message}, timeout=CHAT_TIMEOUT))
    except CoachError:
        if _still_building(row.agent_id):
            raise CoachError("Your coach is still being built on Maritime (a few minutes the first time). Try again shortly.") from None
        raise


def _still_building(agent_id: str) -> bool:
    try:
        status = str(_maritime("GET", f"/api/agents/{agent_id}").get("status", "")).lower()
    except CoachError:
        return False
    return status in ("creating", "pending", "provisioning", "building", "deploying", "starting", "queued")


# ---------------------------------------------------------------------------------------------------- what it's told
def _readable(slug: str | None) -> str:
    return re.sub(r"[-_]+", " ", (slug or "").split("/")[-1]).strip().capitalize()


def snapshot(db: Session, user: User) -> dict[str, Any]:
    """Edify's current picture of the student, for the coach's memory. No email, phone or anything it doesn't need."""
    weak = db.scalars(select(WeakTopic).where(WeakTopic.user_id == user.id, WeakTopic.status == "open")
                      .order_by(WeakTopic.misses.desc()).limit(12)).all()
    mocks = db.scalars(select(MockTest).where(MockTest.user_id == user.id, MockTest.status == "submitted")
                       .order_by(MockTest.submitted_at.desc()).limit(5)).all()
    sessions = db.scalars(select(StudySession).where(StudySession.user_id == user.id, StudySession.ended_at.is_not(None))
                          .order_by(StudySession.ended_at.desc()).limit(8)).all()
    return {
        "type": "sync",
        "student": {"name": (user.full_name or "").split(" ")[0], "exam": user.exam_target, "language": user.language},
        "weak": [{"chapter": _readable(w.chapter_id), "topic": _readable(w.topic_id) or None, "misses": w.misses,
                  "note": (w.note or "")[:200]} for w in weak],
        "mocks": [{"title": m.title, "score": m.score, "max_score": m.max_score, "submitted_at": m.submitted_at} for m in mocks],
        "sessions": [{"title": s.title, "subject": s.subject, "ended_at": s.ended_at} for s in sessions],
    }


def lecture_event(s: StudySession) -> dict[str, Any]:
    return {"type": "lecture_done", "lecture": {"id": s.id, "title": s.title or "Lecture", "subject": s.subject,
                                                "summary_md": (s.summary or "")[:6000], "ended_at": s.ended_at}}


# ---------------------------------------------------------------------------------------------------- the API's verbs
def row_of(db: Session, user: User) -> CoachAgent | None:
    return db.get(CoachAgent, user.id)


def view(db: Session, user: User) -> dict[str, Any]:
    row = row_of(db, user)
    m = mode()
    return {"available": m is not None, "on_maritime": m == "maritime", "enabled": row is not None,
            "status": row.status if row else None, "error": row.error if row else None,
            "state": (row.state or {}) if row else {}, "synced_at": row.synced_at if row else None}


def _keep(db: Session, row: CoachAgent, reply: dict[str, Any]) -> None:
    if isinstance(reply.get("state"), dict):
        row.state = reply["state"]
    row.status, row.error, row.synced_at = "ready", None, utcnow()
    db.commit()


def enable(db: Session, user: User) -> dict[str, Any]:
    m = mode()
    if m is None:
        raise CoachError("Edify Coach isn't switched on for this server yet.")
    row = row_of(db, user) or CoachAgent(user_id=user.id, mode=m)
    row.mode = m
    db.add(row)
    if m == "maritime" and not row.agent_id:
        try:
            row.agent_id = _provision(user)
        except CoachError as exc:
            row.status, row.error = "failed", str(exc)
            db.commit()
            raise
    row.status = "starting"
    db.commit()
    try:
        refresh(db, user)
    except CoachError as exc:  # a brand-new machine is often still building: the row says so, and a retry finishes it
        row.error = str(exc)
        db.commit()
    return view(db, user)


def refresh(db: Session, user: User) -> dict[str, Any]:
    """Tell the coach what's new, then have it plan the day."""
    row = _require(db, user)
    _send(row, snapshot(db, user))
    _keep(db, row, _send(row, {"type": "review", "reason": "asked"}))
    return view(db, user)


def ask(db: Session, user: User, question: str) -> str:
    row = _require(db, user)
    reply = _send(row, {"type": "ask", "question": question})
    _keep(db, row, reply)
    return str(reply.get("answer") or "")


def revised(db: Session, user: User, lecture_id: str) -> dict[str, Any]:
    row = _require(db, user)
    _keep(db, row, _send(row, {"type": "revised", "lecture_id": lecture_id}))
    return view(db, user)


def _require(db: Session, user: User) -> CoachAgent:
    row = row_of(db, user)
    if row is None:
        raise CoachError("Turn on your coach first.")
    return row


# ---------------------------------------------------------------------------------------------------- after a lecture
def lecture_finished(user_id: int, session_id: int) -> None:
    """In the background, after a lecture ends: the coach gets the lecture and writes its revision pack. Never
    slows or breaks ending a lecture (a student without a coach costs one primary-key lookup)."""
    if mode() is None:
        return

    def run() -> None:
        with SessionLocal() as db:
            row = db.get(CoachAgent, user_id)
            user = db.get(User, user_id)
            s = db.get(StudySession, session_id)
            if row is None or user is None or s is None:
                return
            try:
                _send(row, snapshot(db, user))
                _keep(db, row, _send(row, lecture_event(s)))
            except CoachError as exc:
                log.info("coach for user %s missed lecture %s: %s", user_id, session_id, exc)

    threading.Thread(target=run, name="edify-coach", daemon=True).start()


def iso(value: datetime | None) -> str | None:
    return value.isoformat() + "Z" if value else None
