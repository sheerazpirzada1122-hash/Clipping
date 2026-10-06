"""
Download YouTube videos or accept local files.
"""
import os
import yt_dlp
from pathlib import Path
from src.config import OUTPUT_DIR, YT_COOKIES_FILE


def download_youtube(url: str, output_dir: Path = OUTPUT_DIR) -> str:
    """
    Download a YouTube video using yt-dlp.
    Returns the local path to the downloaded file.
    """
    output_template = str(output_dir / "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    if YT_COOKIES_FILE and os.path.exists(YT_COOKIES_FILE):
        ydl_opts["cookiefile"] = YT_COOKIES_FILE

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info["id"]
        creator = info.get("uploader") or info.get("channel") or "Unknown"
        title = info.get("title", "")

    # Find the downloaded file
    for ext in ("mp4", "mkv", "webm"):
        candidate = output_dir / f"{video_id}.{ext}"
        if candidate.exists():
            # Persist metadata for later use
            meta_path = output_dir / f"{video_id}.meta"
            meta_path.write_text(f"{creator}\n{title}\n", encoding="utf-8")
            return str(candidate)

    raise FileNotFoundError(f"Download failed for {url}")


def resolve_input(source: str) -> str:
    """
    Accept either a YouTube URL or a local file path.
    Returns a local video path.
    """
    if source.startswith(("http://", "https://", "www.")):
        return download_youtube(source)
    if os.path.exists(source):
        return source
    raise FileNotFoundError(f"Invalid source: {source}")
