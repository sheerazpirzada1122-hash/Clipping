"""
Whisper-based transcription with word-level timestamps.
"""
import json
from pathlib import Path
import whisper
from src.config import WHISPER_MODEL, OUTPUT_DIR


def transcribe(video_path: str, model_name: str = WHISPER_MODEL) -> dict:
    """
    Transcribe a video using OpenAI Whisper.
    Returns a dict with 'text', 'segments', and 'words' (word-level).
    """
    print(f"[Transcriber] Loading Whisper model: {model_name}")
    model = whisper.load_model(model_name)

    print(f"[Transcriber] Transcribing {video_path} ...")
    result = model.transcribe(
        video_path,
        language="en",
        word_timestamps=True,
        verbose=False,
    )

    # Flatten word list
    words = []
    for seg in result["segments"]:
        for w in seg.get("words", []):
            words.append({
                "word": w["word"].strip(),
                "start": float(w["start"]),
                "end": float(w["end"]),
            })

    payload = {
        "text": result["text"].strip(),
        "segments": result["segments"],
        "words": words,
    }

    # Cache transcript
    cache_path = Path(video_path).with_suffix(".transcript.json")
    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[Transcriber] Saved transcript to {cache_path}")
    return payload
