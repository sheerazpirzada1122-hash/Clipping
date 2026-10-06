"""
Central configuration module.
Loads environment variables and defines global constants.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
OUTPUT_DIR = ROOT_DIR / "output"
BROLL_DIR = ASSETS_DIR / "broll"
FONT_PATH = ASSETS_DIR / "fonts" / "Montserrat-ExtraBold.ttf"

OUTPUT_DIR.mkdir(exist_ok=True)

# --- Video settings ---
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30
SPEED_FACTOR = 1.03          # Fair-use speed tweak (1.02 - 1.05)
PITCH_SEMITONES = 0.4        # Subtle audio pitch shift
CLIP_MIN_DURATION = 30
CLIP_MAX_DURATION = 60

# --- Transcription ---
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# --- YouTube OAuth ---
YT_CLIENT_SECRET_FILE = os.getenv("YT_CLIENT_SECRET", "client_secret.json")
YT_REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN", "")
YT_TOKEN_FILE = OUTPUT_DIR / "yt_token.json"

# --- OpenAI (optional, for metadata generation) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
