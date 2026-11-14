"""Data rights: export everything, delete everything."""
from tests.conftest import board_png


def _register(client, email):
    r = client.post("/api/auth/register", json={"accepted_terms": True, "email": email, "full_name": "Ira Shah", "password": "correct-horse-1",
                                                 "exam_target": "neet"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_export_and_delete_account(client):
    h = _register(client, "ira@example.com")
    s = client.post("/api/sessions", headers=h, json={"title": "Cell biology"}).json()
    img = board_png(["Mitochondria", "Powerhouse of the cell", "ATP synthesis"])
    assert client.post(f"/api/capture/{s['id']}/frame", headers=h, files={"frame": ("f.png", img, "image/png")}).status_code == 200
    client.post("/api/quiz/attempt", headers=h, json={"question": "q", "q_type": "mcq", "correct": False})
    client.post("/api/flashcards", headers=h, json={"front": "ATP?", "back": "Energy currency"})
    code = client.post("/api/rooms", headers=h, json={"name": "Bio squad"}).json()["code"]

    r = client.get("/api/auth/export", headers=h)
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    data = r.json()
    assert data["profile"]["email"] == "ira@example.com" and "hashed_pw" not in str(data)
    assert data["lectures"][0]["title"] == "Cell biology" and data["lectures"][0]["boards"]
    assert data["answers"] and data["flashcards"]

    assert client.post("/api/auth/delete-account", headers=h, json={"password": "correct-horse-1", "confirm": "delete"}).status_code == 422
    assert client.post("/api/auth/delete-account", headers=h, json={"password": "wrong-password", "confirm": "DELETE"}).status_code == 400
    assert client.post("/api/auth/delete-account", headers=h, json={"password": "correct-horse-1", "confirm": "DELETE"}).status_code == 204

    assert client.post("/api/auth/login", json={"email": "ira@example.com", "password": "correct-horse-1"}).status_code == 401
    assert client.get("/api/auth/me", headers=h).status_code == 401
    other = _register(client, "ira2@example.com")
    assert client.post("/api/rooms/join", headers=other, json={"code": code}).status_code == 404


def test_deleting_an_account_with_payments(client):
    """An open, unpaid checkout used to block deleting the account (payments pointed at the user). A paid one is kept
    for the accounts, on a row with no name, email or way to sign in."""
    from app.core.database import SessionLocal
    from app.models.payment import Payment
    from app.models.user import User

    for email, status in (("unpaid@example.com", "created"), ("paid@example.com", "paid")):
        h = _register(client, email)
        uid = client.get("/api/auth/me", headers=h).json()["id"]
        with SessionLocal() as db:
            db.add(Payment(user_id=uid, purpose="pro_month", amount_inr=249, provider="razorpay", status=status))
            db.commit()
        assert client.post("/api/auth/delete-account", headers=h, json={"password": "correct-horse-1", "confirm": "DELETE"}).status_code == 204
        with SessionLocal() as db:
            user = db.get(User, uid)
            kept = db.query(Payment).filter(Payment.user_id == uid).count()
            if status == "created":
                assert user is None and kept == 0
            else:
                assert kept == 1 and user.email.endswith("@deleted.invalid") and user.full_name == "Deleted account" and not user.is_active
        assert client.post("/api/auth/login", json={"email": email, "password": "correct-horse-1"}).status_code == 401


def test_deleting_an_account_takes_its_root_traces_and_coach(client):
    """Root-cause traces and the coach's record point at the student: deleting the account must take them too (on
    Postgres a trace left behind blocked the delete with a foreign-key error; SQLite here doesn't enforce it)."""
    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.models.coach import CoachAgent
    from app.models.gap import GapTrace

    r = client.post("/api/auth/register", json={"accepted_terms": True, "email": "traced@example.com", "full_name": "Traced Student",
                                                "password": "correct-horse-1", "exam_target": "jee"})
    h, uid = {"Authorization": f"Bearer {r.json()['access_token']}"}, r.json()["user"]["id"]
    with SessionLocal() as db:
        db.add_all([GapTrace(user_id=uid, chapter_id="physics.rotational-motion", title="Rotational Motion", chain=[], status="clear"),
                    CoachAgent(user_id=uid, mode="local", status="ready")])
        db.commit()
    assert client.post("/api/auth/delete-account", headers=h, json={"password": "correct-horse-1", "confirm": "DELETE"}).status_code == 204
    with SessionLocal() as db:
        assert db.scalar(select(GapTrace).where(GapTrace.user_id == uid)) is None
        assert db.get(CoachAgent, uid) is None


def test_deleting_an_account_takes_its_senior_posts(client):
    """A question someone asked under "Ask a senior", the answers under it, and their own answers elsewhere go with
    their account (on Postgres a post left behind blocked the delete)."""
    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.models.campus import CampusPost

    def register(email, name):
        r = client.post("/api/auth/register", json={"accepted_terms": True, "email": email, "full_name": name,
                                                    "password": "correct-horse-1", "exam_target": "college_cse"})
        return {"Authorization": f"Bearer {r.json()['access_token']}"}, r.json()["user"]["id"]

    h, uid = register("asker@example.com", "Asker Student")
    _, other = register("helper@example.com", "Helper Senior")
    with SessionLocal() as db:
        theirs = CampusPost(user_id=uid, subject="Data Structures", kind="question", body="How do I revise trees?")
        elsewhere = CampusPost(user_id=other, subject="Data Structures", kind="question", body="Graphs or DP first?")
        db.add_all([theirs, elsewhere])
        db.flush()
        db.add_all([CampusPost(user_id=other, subject="Data Structures", kind="answer", parent_id=theirs.id, body="Draw them."),
                    CampusPost(user_id=uid, subject="Data Structures", kind="answer", parent_id=elsewhere.id, body="Graphs.")])
        db.commit()
        kept = elsewhere.id
    assert client.post("/api/auth/delete-account", headers=h, json={"password": "correct-horse-1", "confirm": "DELETE"}).status_code == 204
    with SessionLocal() as db:
        left = db.scalars(select(CampusPost)).all()
        assert all(p.user_id != uid for p in left)  # nothing of theirs
        assert [p.id for p in left if p.subject == "Data Structures"] == [kept]  # the other student's question stays


def test_deleting_an_account_removes_its_maritime_end_user(client, monkeypatch):
    """A student registered on Maritime (name and limits) is removed there too when they delete their account."""
    import httpx

    from app.core.config import settings
    from app.core.database import SessionLocal
    from app.models.coach import CoachAgent
    from app.services import coach

    calls = []
    monkeypatch.setattr(settings, "MARITIME_API_KEY", "mk_test")
    monkeypatch.setattr(coach.httpx, "request", lambda method, url, **k: calls.append((method, url)) or httpx.Response(204, request=httpx.Request(method, url)))
    r = client.post("/api/auth/register", json={"accepted_terms": True, "email": "maritime.leaver@example.com", "full_name": "Leaving Student",
                                                "password": "correct-horse-1", "exam_target": "jee"})
    h, uid = {"Authorization": f"Bearer {r.json()['access_token']}"}, r.json()["user"]["id"]
    with SessionLocal() as db:
        db.add(CoachAgent(user_id=uid, mode="local", status="ready", maritime_user=f"edify_{uid}"))
        db.commit()
    assert client.post("/api/auth/delete-account", headers=h, json={"password": "correct-horse-1", "confirm": "DELETE"}).status_code == 204
    assert calls == [("DELETE", f"{settings.MARITIME_API_URL}/api/v1/end-users/edify_{uid}")]


def test_without_the_manage_scope_the_maritime_name_is_blanked_instead(monkeypatch):
    """Edify's Maritime key may not be allowed to delete end users: then nothing personal is left there either."""
    import httpx

    from app.core.config import settings
    from app.services import coach

    calls = []

    def fake(method, url, json=None, **k):  # noqa: A002 - httpx's own name
        calls.append((method, json))
        status = 403 if method == "DELETE" else 200
        return httpx.Response(status, json={"detail": "This API key lacks the 'manage' scope"} if status == 403 else {}, request=httpx.Request(method, url))

    monkeypatch.setattr(settings, "MARITIME_API_KEY", "mk_test")
    monkeypatch.setattr(coach.httpx, "request", fake)
    coach.forget(42)
    assert calls[0] == ("DELETE", None)
    assert calls[1][0] == "PUT" and calls[1][1]["displayName"] == "Deleted student" and calls[1][1]["metadata"] == {}
