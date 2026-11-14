"""Innovation #2 for teachers: where a batch's trouble really starts. Each student's root-cause traces are added up by
the earlier chapter they led to, so a teacher sees "most of the students stuck on Rotational Motion are missing Class 10
trigonometry", with nobody named."""
from app.core.database import SessionLocal
from app.models.gap import GapTrace
from app.services import gaps


def _user(client, email, name):
    r = client.post("/api/auth/register", json={"accepted_terms": True, "email": email, "full_name": name,
                                                "password": "correct-horse-1", "exam_target": "jee"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, r.json()["user"]["id"]


def _link(chapter_id, name, cls, idea, result):
    return {"chapter_id": chapter_id, "name": name, "subject": "Mathematics", "cls": cls, "idea": idea, "why": "",
            "check": {"q": "?", "options": ["a", "b"], "answer": 0}, "result": result}


TRIG = ("cbse_10.maths.trigonometry", "Introduction to Trigonometry", 10, "sin, cos and tan of an angle")
RATIOS = ("cbse_7.maths.ratios", "Comparing Quantities", 7, "ratios and proportion")


def _trace(uid, title, root, status="found", deeper_ok=True):
    """A trace whose deepest wrong link is ``root`` (None: every link right)."""
    chain = [_link(*TRIG[:3], TRIG[3], "wrong" if root == TRIG else "right"),
             _link(*RATIOS[:3], RATIOS[3], "wrong" if root == RATIOS else "right")]
    index = None if root is None else (0 if root == TRIG else 1)
    return GapTrace(user_id=uid, chapter_id="jee.physics.rotational-motion", title=title, chain=chain, root=index,
                    status=status if root else "clear")


def test_a_teacher_sees_where_the_batch_gaps_start(client):
    teacher, _ = _user(client, "roots.teacher@example.com", "Meera Rao")
    room = client.post("/api/classes", headers=teacher, json={"name": "JEE 2027 batch A"}).json()
    code, class_id = room["code"], room["id"]
    ids = []
    for i in range(5):
        h, uid = _user(client, f"roots.student{i}@example.com", f"Student {i}")
        assert client.post("/api/classes/join", headers=h, json={"code": code}).status_code == 200
        ids.append(uid)
    outsider_h, outsider = _user(client, "roots.outsider@example.com", "Not In Class")
    with SessionLocal() as db:
        db.add_all([
            _trace(ids[0], "Rotational Motion", TRIG),
            _trace(ids[1], "Rotational Motion", TRIG, status="fixed"),
            _trace(ids[2], "Projectile Motion", TRIG),
            _trace(ids[2], "Rotational Motion", TRIG),  # the same student twice counts once
            _trace(ids[3], "Laws of Motion", RATIOS),
            _trace(ids[4], "Rotational Motion", None),  # traced, nothing missing
            _trace(outsider, "Rotational Motion", RATIOS),  # not in the class: not counted
            GapTrace(user_id=ids[4], chapter_id="x", title="Still answering", chain=[], status="checking"),
        ])
        db.commit()
    roots = client.get(f"/api/classes/{class_id}", headers=teacher).json()["roots"]
    assert (roots["traced"], roots["with_root"], roots["fixed"]) == (5, 4, 1)
    first, second = roots["roots"]
    assert first["name"] == "Introduction to Trigonometry" and first["cls"] == 10 and first["students"] == 3
    assert first["fixed"] == 1 and first["share"] == 75 and first["idea"] == "sin, cos and tan of an angle"
    assert first["stuck_on"][0] == "Rotational Motion" and "Projectile Motion" in first["stuck_on"]
    assert second["name"] == "Comparing Quantities" and second["students"] == 1 and second["share"] == 25
    keys = {"chapter_id", "name", "subject", "cls", "idea", "students", "fixed", "share", "stuck_on"}
    assert all(set(r) == keys for r in roots["roots"])  # counts and chapters only: no student ids or names
    # only the class's teacher sees it
    assert client.get(f"/api/classes/{class_id}", headers=outsider_h).status_code in (403, 404)


def test_an_empty_class_has_an_empty_map():
    with SessionLocal() as db:
        assert gaps.batch_roots(db, []) == {"traced": 0, "with_root": 0, "fixed": 0, "roots": []}
