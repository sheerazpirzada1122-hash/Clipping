"""
CLI entry point for the YouTube → Shorts automation pipeline.

Supports two modes:
  1. Single video mode  → process one specific video or local file
  2. Channel mode       → auto-pick the most viral unprocessed video
                          from a YouTube channel

Usage:
  # Single YouTube video (with upload)
  python main.py --source "https://youtu.be/VIDEO_ID" --upload

  # Single local file
  python main.py --source "./my_video.mp4"

  # Channel mode — auto-pick viral video
  python main.py --channel "https://www.youtube.com/@MrBeast" --upload

  # Channel mode with custom scan depth
  python main.py --channel "https://www.youtube.com/@MrBeast" --upload --max-check 50
"""
import argparse
import sys
from rich import print as rprint

# Single video pipeline
from src.pipeline import run as run_single

# Channel pipeline — imported lazily so single-video mode works
# even if channel modules aren't set up yet
def _run_channel_safe(channel_url: str, upload: bool, max_check: int):
    try:
        from src.channel_pipeline import run_channel
    except ImportError as e:
        rprint(f"[red]Channel mode requires additional files:[/red] {e}")
        rprint("[yellow]Make sure these exist:[/yellow]")
        rprint("  - src/channel_fetcher.py")
        rprint("  - src/viral_selector.py")
        rprint("  - src/state_tracker.py")
        rprint("  - src/channel_pipeline.py")
        sys.exit(1)
    run_channel(channel_url, upload=upload, max_check=max_check)


def main():
    parser = argparse.ArgumentParser(
        description="YouTube → Shorts automation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Mutually exclusive: either --source OR --channel (not both)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--source",
        help="YouTube URL or local video file path",
    )
    group.add_argument(
        "--channel",
        help="YouTube channel URL — auto-picks the most viral unprocessed video",
    )

    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload the final Short to YouTube (default: don't upload)",
    )
    parser.add_argument(
        "--max-check",
        type=int,
        default=30,
        help="Channel mode: max recent videos to scan (default: 30)",
    )

    args = parser.parse_args()

    if args.channel is not None:
        args.channel = args.channel.strip()
        if not args.channel:
            rprint("[red]CHANNEL_URL khali hai. GitHub Secret ya input check karein.[/red]")
            sys.exit(1)

    # --- Validate ---
    if args.max_check < 1:
        rprint("[red]--max-check must be >= 1[/red]")
        sys.exit(1)

    # --- Execute ---
    try:
        if args.channel:
            rprint(f"[bold cyan]Mode:[/bold cyan] Channel auto-pick")
            rprint(f"[bold cyan]Channel:[/bold cyan] {args.channel}")
            rprint(f"[bold cyan]Upload:[/bold cyan] {args.upload}")
            rprint(f"[bold cyan]Scan depth:[/bold cyan] {args.max_check} videos\n")
            _run_channel_safe(args.channel, args.upload, args.max_check)
        else:
            rprint(f"[bold cyan]Mode:[/bold cyan] Single video")
            rprint(f"[bold cyan]Source:[/bold cyan] {args.source}")
            rprint(f"[bold cyan]Upload:[/bold cyan] {args.upload}\n")
            run_single(args.source, upload=args.upload)

    except KeyboardInterrupt:
        rprint("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(130)
    except Exception as e:
        rprint(f"\n[bold red]❌ Pipeline failed:[/bold red] {e}")
        stderr = getattr(e, "stderr", None)
        if stderr:
            print(stderr.decode(errors="ignore")[-3000:])
        raise


if __name__ == "__main__":
    main()
