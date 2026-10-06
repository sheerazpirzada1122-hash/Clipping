"""
Track which videos have already been processed.
Uses a simple JSON file that gets committed back to the repo.
"""
import json
from pathlib import Path
from typing import Set

STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "processed.json"


def load_processed() -> Set[str]:
    """Return set of video IDs already processed."""
    if not STATE_FILE.exists():
        return set()
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return set(data.get("processed", []))
    except Exception:
        return set()


def mark_processed(video_id: str, metadata: dict = None):
    """Add a video ID to the processed list and save."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"processed": []}
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {"processed": []}

    if video_id not in data["processed"]:
        data["processed"].append(video_id)
    if metadata:
        data.setdefault("history", []).append({
            "id": video_id,
            **metadata,
        })
    STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[State] Marked {video_id} as processed.")
