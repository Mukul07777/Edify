"""Silent tracing: Edify suspects a root gap from the weak spots a student already has, before any quiz. Two weak
exam chapters resting on the same earlier chapter point at it; one alone is not enough; roots already traced drop out.
The coach plans a two-minute check on the likeliest one."""
import importlib.util
import os
import tempfile
from pathlib import Path

from app.core.database import SessionLocal
from app.models.gap import GapTrace, PrereqMap
from app.models.weak import WeakTopic
from app.services import gaps, syllabus

AGENT = Path(__file__).resolve().parents[2] / "agents" / "edify-coach" / "server.py"


def _user(client, email):
    r = client.post("/api/auth/register", json={"accepted_terms": True, "email": email, "full_name": "Asha K",
                                                "password": "correct-horse-1", "exam_target": "jee"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, r.json()["user"]["id"]


def _link(cid, name, cls, result=None):
    out = {"chapter_id": cid, "name": name, "subject": "Mathematics", "cls": cls, "idea": f"{name} idea", "why": "",
           "check": {"q": "?", "options": ["a", "b"], "answer": 0}}
    return {**out, "result": result} if result else out


def test_two_weak_chapters_on_one_foundation_make_a_suspect(client):
    h, uid = _user(client, "suspect.a@example.com")
    a, b, c = [ch.id for ch in syllabus.get("jee").chapters[:3]]
    with SessionLocal() as db:
        db.merge(PrereqMap(key=a, chain=[_link("sx.trig", "Trig X", 10), _link("sx.ratio", "Ratio X", 7)]))
        db.merge(PrereqMap(key=b, chain=[_link("sx.trig", "Trig X", 10)]))
        db.merge(PrereqMap(key=c, chain=[_link("sx.lonely", "Lonely X", 9)]))
        db.add_all([WeakTopic(user_id=uid, chapter_id=a, misses=4, checks=[]), WeakTopic(user_id=uid, chapter_id=b, misses=2, checks=[]),
                    WeakTopic(user_id=uid, chapter_id=c, misses=9, checks=[])])
        db.commit()

    sus = client.get("/api/gaps", headers=h).json()["suspects"]
    assert [s["chapter_id"] for s in sus] == ["sx.trig"]        # shared by two weak chapters; Ratio and Lonely only one
    assert sus[0]["trace_chapter_id"] == a and sus[0]["misses"] == 6 and len(sus[0]["because"]) == 2

    with SessionLocal() as db:  # once traced and shown to hold, it is no longer suspected
        db.add(GapTrace(user_id=uid, chapter_id=a, title="t", chain=[_link("sx.trig", "Trig X", 10, "right")], root=None, status="clear"))
        db.commit()
    assert client.get("/api/gaps", headers=h).json()["suspects"] == []


def test_one_weak_chapter_suspects_nothing(client):
    _, uid = _user(client, "suspect.b@example.com")
    with SessionLocal() as db:
        db.add(WeakTopic(user_id=uid, chapter_id=syllabus.get("jee").chapters[0].id, misses=10, checks=[]))
        db.commit()
        assert gaps.suspects(db, uid, syllabus.get("jee")) == []


def test_the_coach_plans_a_check_on_the_suspect_when_no_root_is_confirmed(monkeypatch):
    monkeypatch.setenv("COACH_DATA", tempfile.mkdtemp(prefix="edify-coach-"))
    spec = importlib.util.spec_from_file_location("edify_coach_suspects", AGENT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mem = {"lectures": [], "suspects": [{"chapter_id": "sx.trig", "name": "Trigonometry", "cls": 10, "idea": "sin and cos",
                         "because": ["Rotational Motion", "Waves"], "trace_chapter_id": "physics.rotational-motion"}]}
    items = mod.review(mem, {"reason": "ask"})["plan"]["items"]
    check = [i for i in items if i["kind"] == "root_check"]
    assert check and check[0]["chapter_id"] == "physics.rotational-motion" and "Class 10 Trigonometry" in check[0]["why"]

    mem2 = {**mem, "gaps": [{"root": "ratios", "stuck_on": "Torque", "chapter": "Ratios", "cls": 7, "trace_id": 1}]}
    assert not [i for i in mod.review(mem2, {"reason": "ask"})["plan"]["items"] if i["kind"] == "root_check"]
