"""
Fair-use transformation utilities:
  - Speed tweak (video + audio)
  - Pitch shift (audio)
  - Color grading
  - Dynamic zoom (Ken Burns)
"""
import ffmpeg
from src.config import SPEED_FACTOR, PITCH_SEMITONES


def apply_speed_and_pitch(input_path: str, output_path: str,
                          speed: float = SPEED_FACTOR,
                          semitones: float = PITCH_SEMITONES) -> str:
    """
    Apply subtle speed change and pitch shift to evade Content ID.
    Video and audio are sped up by `speed`; audio pitch is shifted by `semitones`.
    """
    # atempo handles speed; asetrate+aresample handles pitch.
    # Combine both into a filter chain.
    pitch_ratio = 2 ** (semitones / 12.0)

    audio_filter = (
        f"aresample=44100,"
        f"asetrate=44100*{pitch_ratio},"
        f"aresample=44100,"
        f"atempo={speed / pitch_ratio:.5f}"
    )

    (
        ffmpeg
        .input(input_path)
        .output(
            output_path,
            vf=f"setpts=PTS/{speed}",
            af=audio_filter,
            video_bitrate="6M",
            audio_bitrate="192k",
            preset="medium",
            **{"c:v": "libx264", "c:a": "aac"},
        )
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path


def apply_color_grade(input_path: str, output_path: str) -> str:
    """
    Apply a subtle cinematic color grade:
    slight contrast boost + warm tint + vignette.
    """
    vf = (
        "eq=contrast=1.08:saturation=1.15:brightness=0.02,"
        "colorbalance=rs=0.03:gs=0.0:bs=-0.03,"
        "vignette=PI/5"
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
