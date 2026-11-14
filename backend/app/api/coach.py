"""Edify Coach: the student's own study coach on Maritime (see services/coach)."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.ratelimit import limit
from app.models.user import User
from app.services import coach

router = APIRouter(prefix="/coach", tags=["coach"])


def _out(view: dict[str, Any]) -> dict[str, Any]:
    return {**view, "synced_at": coach.iso(view.get("synced_at"))}


def _call(fn, *args):
    try:
        return fn(*args)
    except coach.CoachError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("")
def get_coach(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    """The coach's last plan and revision packs (kept here, so this never waits on a sleeping coach)."""
    return _out(coach.view(db, user))


@router.post("/enable", dependencies=[Depends(limit("coach-enable", 4))])
def enable(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Give the student their own coach (a Maritime machine of their own), then let it plan the day."""
    return _out(_call(coach.enable, db, user))


@router.post("/refresh", dependencies=[Depends(limit("coach-refresh", 6))])
def refresh(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    return _out(_call(coach.refresh, db, user))


class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=1500)


@router.post("/ask", dependencies=[Depends(limit("coach-ask", 10))])
def ask(body: AskIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {"answer": _call(coach.ask, db, user, body.question.strip())}


class RevisedIn(BaseModel):
    lecture_id: str = Field(min_length=1, max_length=40)


@router.post("/revised", dependencies=[Depends(limit("coach-revised", 20))])
def revised(body: RevisedIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    return _out(_call(coach.revised, db, user, body.lecture_id))
