"""The next-class kit: the board that lost the room, turned into a plan for the next class."""
from tests.test_confusion import _boards
from tests.test_rooms_v3 import _register, _room


def _signals(code, note_id):
    from app.core.database import SessionLocal
    from app.models.room import LectureSignal

    with SessionLocal() as db:
        db.add_all([
            LectureSignal(room_code=code, kind="lost", note_id=note_id),
            LectureSignal(room_code=code, kind="lost", note_id=note_id),
            LectureSignal(room_code=code, kind="wrong", note_id=note_id, data={"sure": True}),
            LectureSignal(room_code=code, kind="doubt", note_id=note_id, text="Why sin 2θ and not sin θ?", data={"votes": 3}),
            LectureSignal(room_code=code, kind="quiz", note_id=note_id, text="Range on level ground?",
                          data={"options": ["u²/g", "u² sin 2θ / g", "u sin θ / g", "2u/g"], "counts": [5, 2, 6, 0], "answer_index": 1}),
        ])
        db.commit()


def test_the_host_gets_a_next_class_kit_built_from_the_evidence(client, monkeypatch):
    from app.services import reteach

    host, _ = _register(client, "kit.host@example.com", "Meera Teacher")
    student, _ = _register(client, "kit.student@example.com", "Kabir Student")
    code = _room(client, monkeypatch, host)
    _, board = _boards(code)
    _signals(code, board)
    seen = []

    def fake_json(messages, **kw):
        seen.append(messages[1]["content"])
        return {"misconception": "They think range uses sin θ, not sin 2θ.", "simpler": "Range depends on both the up and the across speed...",
                "analogy": "Throwing a cricket ball to the boundary: 45° goes farthest.", "board_plan": ["R = u² sin 2θ / g", "Max at 45°", "Same R for θ and 90° − θ"],
                "openers": [{"q": "At what angle is the range largest?", "options": ["30°", "45°", "60°", "90°"], "answer": 1, "explain": "sin 2θ = 1"},
                            {"q": "broken"}],
                "root_idea": "double-angle identity sin 2θ", "root_class": 11}

    monkeypatch.setattr(reteach.llm, "json", fake_json)
    r = client.post(f"/api/rooms/{code}/next-class-kit", headers=host, json={"note_id": board})
    assert r.status_code == 200, r.text
    kit = r.json()
    # the model saw the real evidence: which wrong option was popular, the doubt, the taps
    assert "u sin θ / g" in seen[0] and "Why sin 2θ" in seen[0] and "Tapped 'I'm lost': 2" in seen[0]
    assert kit["evidence"] == {"lost": 2, "wrong": 1, "doubts": 1}
    assert len(kit["openers"]) == 1 and kit["openers"][0]["answer"] == 1  # the broken opener is dropped
    assert kit["root_class"] == 11 and kit["board_plan"][1] == "Max at 45°"

    # the same evidence: the same kit, no second AI call
    assert client.post(f"/api/rooms/{code}/next-class-kit", headers=host, json={"note_id": board}).json() == kit
    assert len(seen) == 1
    # only the host gets it; a student never does
    assert client.post(f"/api/rooms/{code}/next-class-kit", headers=student, json={"note_id": board}).status_code == 404
