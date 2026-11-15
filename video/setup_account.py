"""A throwaway demo account for filming the root-cause trace step by step (run from backend/, app on :8011).
Its email starts with demo.edify., so it never counts as a real student. Prints nothing secret."""
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.core.database import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import account, syllabus, weak  # noqa: E402

EMAIL, PW, BASE = "demo.edify.video@example.com", "edify-demo-2026", "http://127.0.0.1:8011"

with SessionLocal() as db:
    old = db.scalar(select(User).where(User.email == EMAIL))
    if old:
        account.delete_everything(db, old)
        db.commit()
r = httpx.post(f"{BASE}/api/auth/register", json={"full_name": "Demo Student (JEE)", "exam_target": "jee", "class_level": "Class 12",
                                                   "email": EMAIL, "password": PW, "accepted_terms": True}, timeout=60)
r.raise_for_status()
h = {"Authorization": f"Bearer {r.json()['access_token']}"}
httpx.patch(f"{BASE}/api/auth/me", headers=h, json={"language": "hinglish"}, timeout=60).raise_for_status()
with SessionLocal() as db:
    u = db.scalar(select(User).where(User.email == EMAIL))
    u.plan = "pro"
    db.commit()
    weak.save_test(db, u.id, syllabus.get("jee"), title="[Demo] Minor Test 3 (Physics)", taken_on=date.today() - timedelta(days=2),
                   score=118, max_score=300, subjects=[{"name": "Physics", "score": 22, "max": 100}], source="manual",
                   weak=[{"chapter_id": "physics.current-electricity", "misses": 4, "note": "Kirchhoff loops and power"},
                         {"chapter_id": "physics.electrostatics", "misses": 3, "note": "Potential and capacitors"},
                         {"chapter_id": "physics.magnetic-effects-of-current-and-magnetism", "misses": 2, "note": "Field of a current loop"}])
    print("ready", u.id)
