"""Edify Coach: the agent (agents/edify-coach/server.py) and Edify's side of it, end to end.

The coach runs for real on a local port with its memory in a temporary folder. Maritime itself is stood in for by a
fake that answers the documented REST calls and passes chat turns to that same coach, so the whole path is
exercised: provisioning (end user, agent from the repo, nightly trigger), sync, review, lecture packs, questions."""
import importlib.util
import json
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest

from app.core.config import settings
from app.services import coach

AGENT = Path(__file__).resolve().parents[2] / "agents" / "edify-coach" / "server.py"


@pytest.fixture(scope="module")
def agent(monkeypatch_module):
    monkeypatch_module.setenv("COACH_DATA", tempfile.mkdtemp(prefix="edify-coach-"))
    for key in ("LLM_API_KEY", "OPENAI_API_KEY"):
        monkeypatch_module.delenv(key, raising=False)  # offline: the coach's own fallbacks answer
    spec = importlib.util.spec_from_file_location("edify_coach_server", AGENT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), mod.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield mod, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


@pytest.fixture(scope="module")
def monkeypatch_module():
    mp = pytest.MonkeyPatch()
    yield mp
    mp.undo()


def test_the_agent_keeps_the_maritime_contract(agent):
    _, url = agent
    assert httpx.get(url + "/health").json()["ok"] is True
    schedules = httpx.get(url + "/schedules").json()
    assert schedules[0]["cron"] and schedules[0]["tz"] == "Asia/Kolkata"
    reply = httpx.post(url + "/chat", json={"message": json.dumps({"type": "state"})}).json()
    assert set(reply) == {"response"} and "state" in json.loads(reply["response"])
    # a schedule's own prompt arrives as text with source "scheduled": the coach treats it as the nightly review
    nightly = json.loads(httpx.post(url + "/chat", json={"message": "run the nightly review", "source": "scheduled"}).json()["response"])
    assert nightly["plan"]["items"]


def _register(client, email):
    r = client.post("/api/auth/register", json={"accepted_terms": True, "email": email, "full_name": "Ravi Kumar",
                                                 "password": "correct-horse-1", "exam_target": "jee"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_off_until_the_server_has_a_coach(client, auth, monkeypatch):
    monkeypatch.setattr(settings, "MARITIME_API_KEY", "")
    monkeypatch.setattr(settings, "MARITIME_COACH_URL", "")
    body = client.get("/api/coach", headers=auth).json()
    assert body["available"] is False and body["enabled"] is False
    assert client.post("/api/coach/enable", headers=auth).status_code == 503


def test_a_coach_on_this_pc(client, agent, monkeypatch):
    _, url = agent
    monkeypatch.setattr(settings, "MARITIME_API_KEY", "")
    monkeypatch.setattr(settings, "MARITIME_COACH_URL", url)
    h = _register(client, "ravi.local@example.com")
    on = client.post("/api/coach/enable", headers=h).json()
    assert on["enabled"] and on["status"] == "ready" and not on["on_maritime"]
    assert on["state"]["plan"]["items"][0]["kind"] == "start"  # nothing studied yet: the coach asks for a lecture

    # a lecture ends: the coach writes its pack, and it falls due for revision tomorrow
    from app.core.database import SessionLocal
    from app.models.session import StudySession
    with SessionLocal() as db:
        uid = client.get("/api/auth/me", headers=h).json()["id"]
        s = StudySession(user_id=uid, title="Rotational motion", subject="Physics", summary="- Torque turns things\n- τ = r × F\n- L = Iω",
                         is_active=False)
        db.add(s)
        db.commit()
        from app.models.user import User
        user = db.get(User, uid)
        coach._keep(db, coach.row_of(db, user), coach._send(coach.row_of(db, user), coach.lecture_event(s)))
    view = client.get("/api/coach", headers=h).json()
    pack = view["state"]["packs"][0]
    assert pack["title"] == "Rotational motion" and "τ = r × F" in pack["formulas"] and len(pack["revise_on"]) == 3

    answer = client.post("/api/coach/ask", headers=h, json={"question": "What should I revise first?"}).json()["answer"]
    assert answer  # offline, the coach still answers (and says the AI is away)

    # one coach on this PC serves every student, but never mixes them: a second student starts with nothing
    other = _register(client, "neha.local@example.com")
    theirs = client.post("/api/coach/enable", headers=other).json()["state"]
    assert theirs["packs"] == [] and theirs["lectures_seen"] == 0
    assert client.get("/api/coach", headers=h).json()["state"]["lectures_seen"] == 1


def test_each_student_gets_their_own_agent_on_maritime(client, agent, monkeypatch):
    mod, _ = agent
    calls: list[tuple[str, str, dict | None]] = []

    def fake(method, url, json=None, timeout=None, headers=None):  # noqa: A002 - httpx's own name
        path = url.removeprefix(settings.MARITIME_API_URL)
        calls.append((method, path, json))
        assert headers["Authorization"] == "Bearer mk_test"
        if path.endswith("/chat"):
            reply = mod.handle(json["message"], None)
            body = {"response": __import__("json").dumps(reply)}
        elif path.endswith("/agents") and method == "POST":
            body = {"id": "agt_123", "status": "deploying"}
        else:
            body = {"ok": True}
        return httpx.Response(200, json=body, request=httpx.Request(method, url))

    monkeypatch.setattr(settings, "MARITIME_API_KEY", "mk_test")
    monkeypatch.setattr(settings, "MARITIME_COACH_REPO", "https://github.com/edify/edify-coach")
    monkeypatch.setattr(settings, "MARITIME_COACH_URL", "")
    monkeypatch.setattr(coach.httpx, "request", fake)
    h = _register(client, "ravi.maritime@example.com")
    uid = client.get("/api/auth/me", headers=h).json()["id"]

    on = client.post("/api/coach/enable", headers=h).json()
    assert on["on_maritime"] and on["status"] == "ready"
    paths = [(m, p) for m, p, _ in calls]
    assert paths[0] == ("PUT", f"/api/v1/end-users/edify_{uid}")
    assert paths[1] == ("POST", f"/api/v1/end-users/edify_{uid}/agents")
    create = calls[1][2]
    assert create["githubRepo"] == "https://github.com/edify/edify-coach" and create["healthCheckPath"] == "/health"
    assert create["tier"] == "smart"  # $1 a month a student, not always_on's $10
    assert paths[2] == ("POST", "/api/agents/agt_123/triggers") and calls[2][2]["type"] == "cron"
    assert ("POST", "/api/agents/agt_123/chat") in paths

    # turning it on again never makes a second machine
    calls.clear()
    client.post("/api/coach/enable", headers=h)
    assert not any(p.endswith("/agents") for _, p, _ in calls)
