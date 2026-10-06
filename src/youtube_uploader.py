"""
YouTube Data API v3 uploader with OAuth refresh-token support.
"""
import os
import json
import pickle
from pathlib import Path
from typing import Dict

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.config import (
    YT_CLIENT_SECRET_FILE, YT_REFRESH_TOKEN, YT_TOKEN_FILE,
)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"


def _load_credentials() -> Credentials:
    """Load credentials from token file or refresh token."""
    creds = None

    # 1) Try cached token
    if YT_TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(YT_TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    # 2) Try refresh token from env (CI-friendly)
    if not creds and YT_REFRESH_TOKEN:
        client_cfg = json.loads(Path(YT_CLIENT_SECRET_FILE).read_text())
        installed = client_cfg.get("installed") or client_cfg.get("web")
        creds = Credentials(
            token=None,
            refresh_token=YT_REFRESH_TOKEN,
            token_uri=installed["token_uri"],
            client_id=installed["client_id"],
            client_secret=installed["client_secret"],
            scopes=SCOPES,
        )

    # 3) Refresh if expired
    if creds and not creds.valid:
        creds.refresh(Request())
        YT_TOKEN_FILE.write_text(creds.to_json())

    # 4) Interactive OAuth as last resort (local dev only)
    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file(
            YT_CLIENT_SECRET_FILE, SCOPES
        )
        creds = flow.run_local_server(port=0)
        YT_TOKEN_FILE.write_text(creds.to_json())

    return creds


def upload_short(video_path: str, metadata: Dict) -> str:
    """
    Upload a Short to YouTube. Returns the video ID.
    """
    creds = _load_credentials()
    youtube = build(API_SERVICE_NAME, API_VERSION, credentials=creds)

    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata.get("tags", []),
            "categoryId": "22",  # People & Blogs
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True,
                            mimetype="video/mp4")
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[Upload] {int(status.progress() * 100)}%")

    print(f"[Upload] Done: https://youtu.be/{response['id']}")
    return response["id"]
