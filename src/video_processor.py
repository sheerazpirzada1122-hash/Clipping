"""
Smart 9:16 vertical framing, overlays, and B-roll/zoom hooks.
"""
import random
from pathlib import Path
from typing import List, Optional
import ffmpeg
from src.config import (
    TARGET_WIDTH, TARGET_HEIGHT, TARGET_FPS,
    BROLL_DIR, FONT_PATH, OUTPUT_DIR,
)


def smart_crop_to_vertical(input_path: str, output_path: str,
                           start: float, end: float) -> str:
    """
    Crop a 16:9 source to 9:16 vertical.
    Strategy: center-crop; zoom slightly to fill the full frame.
    """
    # Crop the largest centered 9:16 region, then scale to target.
    # If the source is wider than 9:16, crop width; else crop height.
    vf = (
        f"crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',"
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={TARGET_WIDTH}:{TARGET_HEIGHT},"
        f"fps={TARGET_FPS}"
    )
    (
        ffmpeg
        .input(input_path, ss=start, to=end)
        .output(output_path, vf=vf,
                **{"c:v": "libx264", "c:a": "aac", "preset": "medium"})
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path


def add_creator_watermark(input_path: str, output_path: str, creator: str) -> str:
    """
    Burn a small attribution overlay: "Original via @Creator".
    Drawn as a semi-transparent banner at the bottom.
    """
    label = f"Original via @{creator}".replace(":", "\\:").replace("'", "")
    # drawtext with a background box
    vf = (
        f"drawtext=fontfile='{FONT_PATH}':"
        f"text='{label}':"
        f"fontcolor=white@0.85:fontsize=36:"
        f"box=1:boxcolor=black@0.45:boxborderw=12:"
        f"x=(w-text_w)/2:y=h-140"
    )
    (
        ffmpeg
        .input(input_path)
        .output(output_path, vf=vf,
                **{"c:v": "libx264", "c:a": "copy", "preset": "medium"})
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path


def add_progress_bar(input_path: str, output_path: str,
                     duration: float) -> str:
    """
    Add a thin animated progress bar at the bottom of the frame.
    Uses the `drawbox` filter with a time-based width expression.
    """
    bar_h = 12
    y = TARGET_HEIGHT - bar_h - 20
    vf = (
        f"drawbox=x=0:y={y}:w='iw*t/{duration:.3f}':h={bar_h}:"
        f"color=yellow@0.9:t=fill"
    )
    (
        ffmpeg
        .input(input_path)
        .output(output_path, vf=vf,
                **{"c:v": "libx264", "c:a": "copy", "preset": "medium"})
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path


def add_dynamic_zoom(input_path: str, output_path: str,
                     segment_duration: float) -> str:
    """
    Add subtle dynamic zoom pulses every ~4 seconds using zoompan.
    Creates visual 'hooks' to retain viewer attention.
    """
    # zoompan with a sinusoidal-ish zoom between 1.0 and 1.08
    vf = (
        "zoompan=z='min(zoom+0.0008,1.08)':"
        "d=1:"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        f"s={TARGET_WIDTH}x{TARGET_HEIGHT}:fps={TARGET_FPS}"
    )
    (
        ffmpeg
        .input(input_path)
        .output(output_path, vf=vf,
                **{"c:v": "libx264", "c:a": "copy", "preset": "medium"})
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path


def pick_broll_clips(count: int = 3) -> List[Path]:
    """Return up to `count` random B-roll files from the assets folder."""
    if not BROLL_DIR.exists():
        return []
    clips = list(BROLL_DIR.glob("*.mp4"))
    random.shuffle(clips)
    return clips[:count]


def add_reaction_banner(input_path: str, output_path: str,
                        text: str, start: float, end: float) -> str:
    """
    Overlay a dynamic commentary/reaction banner for a time window.
    """
    safe = text.replace(":", "\\:").replace("'", "")
    vf = (
        f"drawtext=fontfile='{FONT_PATH}':text='{safe}':"
        f"fontcolor=black:fontsize=54:"
        f"box=1:boxcolor=yellow@0.9:boxborderw=18:"
        f"x=(w-text_w)/2:y=180:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
    )
    (
        ffmpeg
        .input(input_path)
        .output(output_path, vf=vf,
                **{"c:v": "libx264", "c:a": "copy", "preset": "medium"})
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path
