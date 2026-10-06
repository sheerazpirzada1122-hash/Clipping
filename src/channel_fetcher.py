"""
Fetch video list from a YouTube channel using yt-dlp.
No API key needed — works with public channels.
"""
import os
from datetime import datetime, timezone
from typing import List, Dict
import yt_dlp
from src.config import YT_COOKIES_FILE


def fetch_channel_videos(channel_url: str, max_videos: int = 30) -> List[Dict]:
    """
    Get recent videos from a channel with metadata:
    id, title, url, views, duration, upload_date, like_count.

    channel_url examples:
      - https://www.youtube.com/@MrBeast
      - https://www.youtube.com/c/MrBeast
      - https://www.youtube.com/channel/UCX6OQ3DkcsbYNE6H8uQQuVA
      - https://www.youtube.com/@MrBeast/videos
    """
    # Ensure we hit the /videos tab (not shorts/live/playlists)
    if not channel_url.rstrip("/").endswith(("/videos", "/streams", "/shorts")):
        channel_url = channel_url.rstrip("/") + "/videos"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,       # Fast — no full video download
        "playlistend": max_videos,
        "skip_download": True,
    }
    if YT_COOKIES_FILE and os.path.exists(YT_COOKIES_FILE):
        ydl_opts["cookiefile"] = YT_COOKIES_FILE

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)

    videos = []
    for entry in info.get("entries", []):
        if not entry:
            continue
        upload_date = entry.get("upload_date") or ""
        if not upload_date and entry.get("timestamp"):
            upload_date = datetime.fromtimestamp(
                entry["timestamp"], tz=timezone.utc
            ).strftime("%Y%m%d")
        videos.append({
            "id": entry.get("id"),
            "title": entry.get("title", ""),
            "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
            "views": entry.get("view_count") or 0,
            "duration": entry.get("duration") or 0,
            "upload_date": upload_date,
            "channel": info.get("channel") or info.get("uploader") or "",
        })

    print(f"[Channel] Fetched {len(videos)} videos from {channel_url}")
    return videos


def fetch_video_stats(video_url: str) -> Dict:
    """
    Get full metadata for a single video (needed when flat extraction
    doesn't return views/likes).
    """
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
    return {
        "id": info.get("id"),
        "title": info.get("title", ""),
        "views": info.get("view_count") or 0,
        "likes": info.get("like_count") or 0,
        "duration": info.get("duration") or 0,
        "upload_date": info.get("upload_date") or "",
        "channel": info.get("uploader") or "",
    }
