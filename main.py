"""
CLI entry point.

Usage:
  python main.py --source "https://youtu.be/..." --upload
  python main.py --source ./local_video.mp4
"""
import argparse
from src.pipeline import run


def main():
    parser = argparse.ArgumentParser(description="YouTube → Shorts automation pipeline")
    parser.add_argument("--source", required=True,
                        help="YouTube URL or local video path")
    parser.add_argument("--upload", action="store_true",
                        help="Upload the final Short to YouTube")
    args = parser.parse_args()

    run(args.source, upload=args.upload)


if __name__ == "__main__":
    main()
