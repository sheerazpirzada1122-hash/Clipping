"""
Select high-engagement 30-60s segments from the transcript.

Scoring heuristics:
  - Sentence completeness
  - Keyword density (hooks, emotional words)
  - Optimal duration (30-60s)
  - Presence of question/CTA
"""
import re
from typing import List, Dict
from src.config import CLIP_MIN_DURATION, CLIP_MAX_DURATION

HOOK_WORDS = {
    "how", "why", "what", "secret", "never", "always", "stop",
    "everyone", "nobody", "truth", "mistake", "best", "worst",
    "hack", "trick", "should", "must", "need", "want",
}
CTA_WORDS = {
    "subscribe", "follow", "like", "comment", "share", "save",
    "check", "link", "bio", "more", "learn",
}


def _score_sentence(text: str) -> float:
    """Score a sentence by hook/CTA keyword density and length."""
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return 0.0
    hook_hits = sum(1 for t in tokens if t in HOOK_WORDS)
    cta_hits = sum(1 for t in tokens if t in CTA_WORDS)
    density = (hook_hits * 1.5 + cta_hits * 2.0) / len(tokens)
    length_bonus = min(len(tokens) / 20.0, 1.0)
    return density + length_bonus * 0.3


def select_best_segment(transcript: Dict) -> Dict:
    """
    Slide a window across sentences to find the best 30-60s segment.
    Returns {'start': float, 'end': float, 'text': str, 'score': float}.
    """
    segments = transcript["segments"]
    if not segments:
        raise ValueError("Empty transcript")

    best = {"start": 0.0, "end": 0.0, "text": "", "score": -1.0}

    for i, seg in enumerate(segments):
        start = seg["start"]
        text_parts: List[str] = []
        j = i
        while j < len(segments):
            end = segments[j]["end"]
            duration = end - start
            if duration > CLIP_MAX_DURATION:
                break
            text_parts.append(segments[j]["text"].strip())
            if duration >= CLIP_MIN_DURATION:
                combined = " ".join(text_parts)
                # Aggregate score across sentences
                score = sum(_score_sentence(p) for p in text_parts) / len(text_parts)
                # Reward duration near the middle of allowed range
                mid = (CLIP_MIN_DURATION + CLIP_MAX_DURATION) / 2
                duration_bonus = 1.0 - abs(duration - mid) / mid
                score += duration_bonus * 0.5
                # Reward arc completeness: hook at start, CTA at end
                if any(w in text_parts[0].lower() for w in HOOK_WORDS):
                    score += 0.4
                if any(w in text_parts[-1].lower() for w in CTA_WORDS):
                    score += 0.4
                if score > best["score"]:
                    best = {
                        "start": start,
                        "end": end,
                        "text": combined,
                        "score": score,
                    }
            j += 1

    if best["score"] < 0:
        # Fallback: take the first 45 seconds
        best = {
            "start": segments[0]["start"],
            "end": min(segments[0]["start"] + 45, segments[-1]["end"]),
            "text": " ".join(s["text"] for s in segments[:5]),
            "score": 0.0,
        }

    print(f"[Selector] Chosen segment: {best['start']:.1f}s -> {best['end']:.1f}s "
          f"(score={best['score']:.2f})")
    return best


def words_in_range(words: List[Dict], start: float, end: float) -> List[Dict]:
    """Return words whose midpoint falls inside [start, end], re-based to 0."""
    out = []
    for w in words:
        mid = (w["start"] + w["end"]) / 2
        if start <= mid <= end:
            out.append({
                "word": w["word"],
                "start": w["start"] - start,
                "end": w["end"] - start,
            })
    return out
