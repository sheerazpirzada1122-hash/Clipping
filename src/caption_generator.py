"""
Generate ASS subtitles with Alex-Hormozi-style word highlighting.
"""
from pathlib import Path
from typing import List, Dict
from src.config import FONT_PATH, TARGET_WIDTH, TARGET_HEIGHT

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat ExtraBold,110,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,2,60,60,320,1
Style: Highlight,Montserrat ExtraBold,120,&H0000FFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,2,60,60,320,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _fmt_time(t: float) -> str:
    """Format seconds as H:MM:SS.cc for ASS."""
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _chunk_words(words: List[Dict], max_words: int = 4) -> List[List[Dict]]:
    """Group words into short chunks (1-4 words) for punchy captions."""
    chunks = []
    for i in range(0, len(words), max_words):
        chunks.append(words[i:i + max_words])
    return chunks


def build_ass(words: List[Dict], output_path: str) -> str:
    """
    Build a styled ASS file with per-word highlighting.
    Each chunk shows all its words, but the active word is highlighted in yellow.
    """
    header = ASS_HEADER.format(w=TARGET_WIDTH, h=TARGET_HEIGHT)
    lines = [header]

    for chunk in _chunk_words(words, max_words=4):
        if not chunk:
            continue
        chunk_start = chunk[0]["start"]
        chunk_end = chunk[-1]["end"]

        # Build a single dialogue line per word so the highlight moves.
        for active_idx, active in enumerate(chunk):
            start = active["start"]
            end = active["end"] if active_idx == len(chunk) - 1 else chunk[active_idx + 1]["start"]
            if end <= start:
                end = start + 0.05

            parts = []
            for i, w in enumerate(chunk):
                if i == active_idx:
                    parts.append(r"{\c&H00FFFF&\fscx115\fscy115}" + w["word"] + r"{\r}")
                else:
                    parts.append(w["word"])
            text = " ".join(parts)
            lines.append(
                f"Dialogue: 0,{_fmt_time(start)},{_fmt_time(end)},Default,,0,0,0,,{text}"
            )

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"[Captions] Wrote ASS -> {output_path}")
    return output_path


def burn_subtitles(video_path: str, ass_path: str, output_path: str) -> str:
    """Burn ASS subtitles directly into the video using FFmpeg."""
    import ffmpeg
    # Escape path for FFmpeg filter on all platforms
    safe_path = ass_path.replace("\\", "/").replace(":", r"\:")
    (
        ffmpeg
        .input(video_path)
        .output(
            output_path,
            vf=f"ass='{safe_path}'",
            **{"c:v": "libx264", "c:a": "copy", "preset": "medium"},
        )
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path
