"""The marked answers of a trace's questions, for the filming script: python answers.py <trace_id> (run from backend/)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.core.database import SessionLocal  # noqa: E402
from app.models.gap import GapTrace  # noqa: E402

with SessionLocal() as db:
    t = db.get(GapTrace, int(sys.argv[1]))
    r = t.retest or {}
    print(json.dumps({
        "status": t.status,
        "before": [i["answer"] for i in (r.get("before") or {}).get("items", [])],
        "after": [i["answer"] for i in (r.get("after") or {}).get("items", [])],
        "chain": [l["check"]["answer"] for l in t.chain],
        "chapters": [l["chapter_id"] for l in t.chain],
        "lesson": (t.lesson or {}).get("check", {}).get("answer"),
    }))
