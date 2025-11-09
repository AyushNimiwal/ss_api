import os
import time
from typing import Optional, List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

YT_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

class YTManager:
    """
    Manage YouTube calls using a user's stored refresh_token + client credentials.
    """

    def __init__(self, credentials: Optional[Credentials] = None):
        self._creds = credentials
        self._youtube = None

    def set_credentials(self, creds: Credentials):
        self._creds = creds
        self._youtube = None

    def _get_service(self):
        if self._youtube is None:
            if not self._creds:
                raise ValueError("No credentials set")
            self._youtube = build("youtube", "v3", credentials=self._creds)
        return self._youtube

    def _refresh_if_needed(self, client_id: str, client_secret: str):
        """
        Ensure self._creds has a valid access token. If expired or missing token,
        refresh using refresh_token.
        """
        if not self._creds:
            raise ValueError("No credentials to refresh")

        if not self._creds.valid:
            if self._creds.expired and self._creds.refresh_token:
                # refresh in place
                request = Request()
                self._creds.refresh(request)
            else:
                # if no refresh_token or not expired state, attempt refresh via explicit token endpoint creation
                # (Normally refresh_token exists; if not, re-auth required)
                raise ValueError("Credentials invalid and cannot refresh automatically")

        # clear cached service so build uses fresh credentials
        self._youtube = None

    def build_credentials_from_refresh(self, refresh_token: str, client_id: str, client_secret: str) -> Credentials:
        """
        Construct a Credentials object using refresh_token and immediately refresh it to get access_token.
        """
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=YT_SCOPES
        )
        # refresh to populate access token
        request = Request()
        creds.refresh(request)
        self.set_credentials(creds)
        return creds

    # ------- API wrappers with simple retry -------
    def _retry_on_http_error(fn):
        def wrapper(self, *args, **kwargs):
            retries = kwargs.pop("_retries", 3)
            backoff = kwargs.pop("_backoff", 1.0)
            for i in range(1, retries + 1):
                try:
                    return fn(self, *args, **kwargs)
                except HttpError as e:
                    if i == retries:
                        raise
                    time.sleep(backoff * (2 ** (i - 1)))
        return wrapper

    @_retry_on_http_error
    def subscriptions_list(self, max_results: int = 50) -> List[Dict[str, Any]]:
        service = self._get_service()
        items = []
        next_token = None
        while True:
            resp = service.subscriptions().list(
                part="snippet,contentDetails",
                mine=True,
                maxResults=max_results,
                pageToken=next_token
            ).execute()
            items.extend(resp.get("items", []))
            next_token = resp.get("nextPageToken")
            if not next_token:
                break
        return items

    @_retry_on_http_error
    def get_channel_videos(self, channel_id: str, max_per_call: int = 50) -> List[Dict[str, Any]]:
        service = self._get_service()
        # get uploads playlist
        resp = service.channels().list(part="contentDetails", id=channel_id).execute()
        items = resp.get("items", [])
        if not items:
            return []
        uploads_playlist = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

        video_items = []
        next_token = None
        while True:
            resp = service.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist,
                maxResults=max_per_call,
                pageToken=next_token
            ).execute()
            video_items.extend(resp.get("items", []))
            next_token = resp.get("nextPageToken")
            if not next_token:
                break
        return video_items