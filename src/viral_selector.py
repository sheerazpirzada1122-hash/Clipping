"""
Select the most 'viral' video from a channel based on a scoring formula.
"""
from typing import List, Dict
from datetime import datetime


def _days_since(upload_date: str) -> int:
    """upload_date format: YYYYMMDD"""
    if not upload_date or len(upload_date) != 8:
        return 999
    try:
        dt = datetime.strptime(upload_date, "%Y%m%d")
        return max((datetime.now() - dt).days, 1)
    except Exception:
        return 999


def score_video(video: Dict) -> float:
    """
    Viral score formula:
      - Views per day (velocity) — most important
      - View count (raw popularity)
      - Optimal duration 5-20 min (long enough for good clip, short enough to process fast)
      - Recency bonus
    """
    views = video.get("views", 0)
    days = _days_since(video.get("upload_date", ""))
    duration = video.get("duration", 0)

    velocity = views / days                       # views per day
    velocity_score = min(velocity / 10000, 10.0)  # cap at 10
    views_score = min(views / 1_000_000, 10.0)    # cap at 10

    # Duration preference: 5-20 minutes
    if 300 <= duration <= 1200:
        duration_score = 3.0
    elif 120 <= duration <= 1800:
        duration_score = 1.5
    else:
        duration_score = 0.5

    # Recency bonus (last 30 days)
    recency_score = 3.0 if days <= 30 else (1.0 if days <= 90 else 0.0)

    return velocity_score * 0.5 + views_score * 0.3 + duration_score + recency_score


def select_viral_video(videos: List[Dict],
                       already_processed: set,
                       min_duration: int = 120) -> Dict:
    """
    Return the highest-scoring video that hasn't been processed yet.
    Skips videos shorter than `min_duration` (too short for a 30-60s clip).
    """
    candidates = [
        v for v in videos
        if v.get("id") not in already_processed
        and v.get("duration", 0) >= min_duration
    ]

    if not candidates:
        print("[Viral] No new videos to process.")
        return {}

    scored = [(score_video(v), v) for v in candidates]
    scored.sort(key=lambda x: x[0], reverse=True)

    best_score, best_video = scored[0]
    print(f"[Viral] Selected: '{best_video['title']}' "
          f"(score={best_score:.2f}, views={best_video['views']:,}, "
          f"duration={best_video['duration']}s)")
    return best_video
