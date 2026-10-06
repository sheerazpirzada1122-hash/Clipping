"""
Generate SEO-optimized YouTube Shorts metadata (title, description, tags).
Falls back to heuristic templates if OpenAI is not configured.
"""
import os
import re
from typing import Dict, List
from src.config import OPENAI_API_KEY

SHORTS_TAGS = [
    "shorts", "viral", "trending", "fyp", "reels",
    "tiktok", "youtubeshorts", "shortsvideo",
]


def _fallback_metadata(transcript_text: str, creator: str) -> Dict:
    """Heuristic metadata generator (no API required)."""
    words = re.findall(r"\w+", transcript_text)
    # Pick the most "hooky" first sentence
    first_sentence = transcript_text.split(".")[0][:80].strip() or "Watch this!"
    title = f"{first_sentence} #shorts"

    # Extract keywords (crude frequency filter)
    stop = {"the", "a", "an", "and", "or", "but", "to", "of", "in", "on",
            "is", "it", "this", "that", "you", "i", "we", "they", "he", "she"}
    freq: Dict[str, int] = {}
    for w in words:
        lw = w.lower()
        if lw in stop or len(lw) < 4:
            continue
        freq[lw] = freq.get(lw, 0) + 1
    top = sorted(freq, key=freq.get, reverse=True)[:10]
    hashtags = " ".join(f"#{t}" for t in top[:5] + SHORTS_TAGS[:3])

    description = (
        f"{first_sentence}\n\n"
        f"🎬 Original video by @{creator}\n"
        f"🔔 Subscribe for more!\n\n"
        f"{hashtags}"
    )
    return {
        "title": title[:100],
        "description": description[:5000],
        "tags": top + SHORTS_TAGS,
    }


def generate_metadata(transcript_text: str, creator: str) -> Dict:
    """
    Generate metadata. Uses OpenAI if available, else falls back to heuristics.
    """
    if not OPENAI_API_KEY:
        print("[Metadata] No OPENAI_API_KEY — using heuristic generator.")
        return _fallback_metadata(transcript_text, creator)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = (
            "You are a YouTube Shorts SEO expert. Given the transcript below, "
            "produce a JSON object with keys: title (<=90 chars, includes #shorts), "
            "description (engaging, includes credit to the original creator, "
            "3-5 hashtags), tags (list of 10-15 strings).\n\n"
            f"Original creator: @{creator}\n\nTranscript:\n{transcript_text[:3000]}"
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        import json
        data = json.loads(resp.choices[0].message.content)
        data.setdefault("tags", SHORTS_TAGS)
        return data
    except Exception as e:
        print(f"[Metadata] OpenAI failed ({e}); using heuristic fallback.")
        return _fallback_metadata(transcript_text, creator)
