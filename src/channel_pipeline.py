"""
Channel → Shorts pipeline.
Picks the most viral unprocessed video from a channel and processes it.
"""
from rich import print as rprint

from src.channel_fetcher import fetch_channel_videos
from src.viral_selector import select_viral_video
from src.state_tracker import load_processed, mark_processed
from src.pipeline import run as run_single_video


def run_channel(channel_url: str, upload: bool = False,
                max_check: int = 30) -> str:
    """
    Full channel pipeline:
      1. Fetch recent videos from channel
      2. Pick the most viral unprocessed one
      3. Run the standard single-video pipeline on it
      4. Mark as processed
    """
    rprint(f"[bold cyan]▶ Channel mode: {channel_url}[/bold cyan]")

    # 1. Fetch
    videos = fetch_channel_videos(channel_url, max_videos=max_check)
    if not videos:
        rprint("[red]No videos found on channel.[/red]")
        return ""

    # 2. Select
    processed = load_processed()
    rprint(f"[dim]Already processed: {len(processed)} videos[/dim]")

    viral = select_viral_video(videos, processed)
    if not viral:
        rprint("[yellow]No new unprocessed videos found.[/yellow]")
        return ""

    # 3. Process
    rprint(f"[bold green]Processing: {viral['title']}[/bold green]")
    output = run_single_video(viral["url"], upload=upload)

    # 4. Mark
    mark_processed(viral["id"], {
        "title": viral["title"],
        "views": viral["views"],
        "url": viral["url"],
    })

    return output
