"""
End-to-end orchestration.
"""
import shutil
from pathlib import Path
from rich import print as rprint

from src.config import OUTPUT_DIR
from src.downloader import resolve_input
from src.transcriber import transcribe
from src.segment_selector import select_best_segment, words_in_range
from src.video_processor import (
    smart_crop_to_vertical, add_creator_watermark,
    add_progress_bar, add_dynamic_zoom, add_reaction_banner,
)
from src.fair_use import apply_speed_and_pitch, apply_color_grade
from src.caption_generator import build_ass, burn_subtitles
from src.metadata_generator import generate_metadata


def _read_creator(video_path: str) -> str:
    meta = Path(video_path).with_suffix(".meta")
    if meta.exists():
        return meta.read_text(encoding="utf-8").splitlines()[0] or "Creator"
    return "Creator"


def run(source: str, upload: bool = False) -> str:
    """
    Full pipeline:
      1. Resolve input (download or local)
      2. Transcribe
      3. Select best 30-60s segment
      4. Crop to 9:16
      5. Fair-use transforms (speed/pitch, color)
      6. Dynamic zoom hooks
      7. Watermark + progress bar + reaction banner
      8. Generate & burn captions
      9. (Optional) Upload to YouTube
    """
    workdir = OUTPUT_DIR / "work"
    workdir.mkdir(exist_ok=True)

    rprint("[bold cyan]▶ Step 1: Resolving input[/bold cyan]")
    video_path = resolve_input(source)
    creator = _read_creator(video_path)
    rprint(f"  Source: {video_path}  |  Creator: @{creator}")

    rprint("[bold cyan]▶ Step 2: Transcribing[/bold cyan]")
    transcript = transcribe(video_path)

    rprint("[bold cyan]▶ Step 3: Selecting best segment[/bold cyan]")
    segment = select_best_segment(transcript)
    words = words_in_range(transcript["words"], segment["start"], segment["end"])

    rprint("[bold cyan]▶ Step 4: Cropping to 9:16[/bold cyan]")
    cropped = workdir / "01_cropped.mp4"
    smart_crop_to_vertical(video_path, str(cropped),
                           segment["start"], segment["end"])

    rprint("[bold cyan]▶ Step 5: Fair-use transforms[/bold cyan]")
    speed = workdir / "02_speed.mp4"
    apply_speed_and_pitch(str(cropped), str(speed))
    graded = workdir / "03_graded.mp4"
    apply_color_grade(str(speed), str(graded))

    rprint("[bold cyan]▶ Step 6: Dynamic zoom hooks[/bold cyan]")
    zoomed = workdir / "04_zoomed.mp4"
    add_dynamic_zoom(str(graded), str(zoomed),
                     segment["end"] - segment["start"])

    rprint("[bold cyan]▶ Step 7: Overlays[/bold cyan]")
    watermark = workdir / "05_watermark.mp4"
    add_creator_watermark(str(zoomed), str(watermark), creator)

    bar = workdir / "06_bar.mp4"
    add_progress_bar(str(watermark), str(bar),
                     (segment["end"] - segment["start"]))

    # Optional: reaction banner in the first 3 seconds (hook)
    banner = workdir / "07_banner.mp4"
    add_reaction_banner(str(bar), str(banner),
                        "WATCH THIS", 0.0, 3.0)

    rprint("[bold cyan]▶ Step 8: Captions[/bold cyan]")
    ass_path = workdir / "captions.ass"
    build_ass(words, str(ass_path))
    final = OUTPUT_DIR / f"short_{Path(video_path).stem}.mp4"
    burn_subtitles(str(banner), str(ass_path), str(final))

    rprint(f"[bold green]✅ Final video: {final}[/bold green]")

    if upload:
        rprint("[bold cyan]▶ Step 9: Uploading to YouTube[/bold cyan]")
        from src.youtube_uploader import upload_short
        metadata = generate_metadata(transcript["text"], creator)
        upload_short(str(final), metadata)

    # Cleanup intermediate files
    shutil.rmtree(workdir, ignore_errors=True)
    return str(final)
