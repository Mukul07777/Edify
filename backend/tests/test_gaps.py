"""Root-cause gap tracing: the chain, the diagnosis, the fix, and what it costs."""
import pytest

from app.services import gaps, syllabus


def _q(answer=1):
    return {"q": "Which is right?", "options": ["a", "b", "c", "d"], "answer": answer, "explain": "because"}


@pytest.fixture
def jee_rotation():
    syl = syllabus.get("jee")
    target = next(c for c in syl.chapters if c.id == "physics.rotational-motion")
    pool = gaps.candidates(syl, target)
    kin = next(c for c in pool if c.id == "physics.kinematics")
    trig10 = next(c for c in pool if c.cls == 10 and "trigonometry" in c.id)
    ratio7 = next(c for c in pool if c.cls == 7 and c.subject == "Mathematics")
    return syl, target, kin, trig10, ratio7


def test_the_pool_reaches_back_into_school_and_stays_on_subject(jee_rotation):
    syl, target, *_ = jee_rotation
    pool = gaps.candidates(syl, target)
    assert target not in pool
    assert {c.subject for c in pool} <= {"Physics", "Mathematics", "Science"}  # never English or History
    assert min(c.cls for c in pool) <= 7 and any(c.cls == 10 for c in pool)


def test_trace_diagnose_fix(client, auth, monkeypatch, jee_rotation):
    syl, target, kin, trig10, ratio7 = jee_rotation
    calls = []

    def fake_json(messages, **kw):
        calls.append(kw.get("feature"))
        if kw.get("feature") == "gap_lesson":
            return {"lesson_md": "Ratios are fractions: $3:4 = 3/4$.\n\nHow this unlocks torque: ...", "check": _q(2)}
        return {"chain": [
            {"chapter_id": kin.id, "idea": "angular velocity", "why": "used directly", "check": _q(1)},
            {"chapter_id": "physics.made-up-chapter", "idea": "invented", "why": "x", "check": _q()},  # not a real chapter
            {"chapter_id": trig10.id, "idea": "sin and cos", "why": "components", "check": {"q": "broken", "options": ["a"]}},  # bad question
            {"chapter_id": trig10.id, "idea": "sin and cos of an angle", "why": "components", "check": _q(0)},
            {"chapter_id": ratio7.id, "idea": "ratios as fractions", "why": "trig ratios are ratios", "check": _q(3)},
        ]}

    monkeypatch.setattr(gaps.llm, "json", fake_json)
    monkeypatch.setattr(syllabus, "of", lambda user, whole=False: syl)

    t = client.post("/api/gaps", headers=auth, json={"chapter_id": target.id})
    assert t.status_code == 200, t.text
    trace = t.json()
    # only real chapters with sound questions, going down through the classes
    assert [link["chapter_id"] for link in trace["chain"]] == [kin.id, trig10.id, ratio7.id]
    assert all("answer" not in link["check"] for link in trace["chain"])  # answers stay on the server

    # right on kinematics, wrong on trig, wrong on ratios: the root is the deepest miss (Class 7 ratios)
    done = client.post(f"/api/gaps/{trace['id']}/answers", headers=auth, json={"answers": [1, 2, 0]}).json()
    assert done["status"] == "found" and done["root"] == 2
    assert done["chain"][2]["check"]["answer"] == 3  # revealed once answered
    assert client.post(f"/api/gaps/{trace['id']}/answers", headers=auth, json={"answers": [1, 1, 3]}).status_code == 400

    fix = client.post(f"/api/gaps/{trace['id']}/lesson", headers=auth).json()
    assert "How this unlocks" in fix["lesson"]["md"] and "answer" not in fix["lesson"]["check"]
    wrong = client.post(f"/api/gaps/{trace['id']}/check", headers=auth, json={"choice": 0}).json()
    assert wrong["status"] == "found" and wrong["lesson"]["result"] == "wrong"
    fixed = client.post(f"/api/gaps/{trace['id']}/check", headers=auth, json={"choice": 2}).json()
    assert fixed["status"] == "fixed"
    assert calls == ["gap_trace", "gap_lesson"]

    # the next student who traces the same chapter, and has the same gap, costs no AI at all
    other = client.post("/api/auth/register", json={"accepted_terms": True, "email": "second.tracer@example.com", "full_name": "Second Tracer",
                                                     "password": "correct-horse-1", "exam_target": "jee"}).json()
    h2 = {"Authorization": f"Bearer {other['access_token']}"}
    t2 = client.post("/api/gaps", headers=h2, json={"chapter_id": target.id}).json()
    client.post(f"/api/gaps/{t2['id']}/answers", headers=h2, json={"answers": [1, 0, 0]})
    assert client.post(f"/api/gaps/{t2['id']}/lesson", headers=h2).json()["lesson"]["md"].startswith("Ratios")
    assert calls == ["gap_trace", "gap_lesson"]
    # and one student never sees another's trace
    assert client.get(f"/api/gaps/{trace['id']}", headers=h2).status_code == 400


def test_all_right_means_the_foundations_hold(client, monkeypatch, jee_rotation):
    syl, target, kin, trig10, _ = jee_rotation
    monkeypatch.setattr(gaps.llm, "json", lambda messages, **kw: {"chain": [
        {"chapter_id": kin.id, "idea": "angular velocity", "why": "", "check": _q(1)},
        {"chapter_id": trig10.id, "idea": "sin and cos", "why": "", "check": _q(0)}]})
    monkeypatch.setattr(syllabus, "of", lambda user, whole=False: syl)
    r = client.post("/api/auth/register", json={"accepted_terms": True, "email": "solid.base@example.com", "full_name": "Solid Base",
                                                 "password": "correct-horse-1", "exam_target": "jee"}).json()
    h = {"Authorization": f"Bearer {r['access_token']}"}
    from app.core.database import SessionLocal
    from app.models.gap import PrereqMap
    with SessionLocal() as db:  # a fresh chain for this test (the one above is shared and cached)
        db.query(PrereqMap).delete()
        db.commit()
    t = client.post("/api/gaps", headers=h, json={"chapter_id": target.id}).json()
    out = client.post(f"/api/gaps/{t['id']}/answers", headers=h, json={"answers": [1, 0]}).json()
    assert out["status"] == "clear" and out["root"] is None
    assert client.post(f"/api/gaps/{t['id']}/lesson", headers=h).status_code == 400  # nothing to fix


def test_the_coach_plans_the_root_first(monkeypatch):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("coach_agent", Path(__file__).resolve().parents[2] / "agents" / "edify-coach" / "server.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "ask_llm", lambda *a, **k: None)
    mem = mod._blank()
    mod.sync(mem, {"gaps": [{"stuck_on": "Rotational Motion", "root": "ratios as fractions", "chapter": "Working with Fractions", "cls": 7, "trace_id": 1}],
                   "weak": [{"chapter": "Rotational motion", "misses": 3}]})
    plan = mod.review(mem, {"reason": "asked"})["plan"]
    assert plan["items"][0]["kind"] == "root" and "ratios as fractions" in plan["items"][0]["title"]
    assert "Class 7" in plan["items"][0]["why"]
