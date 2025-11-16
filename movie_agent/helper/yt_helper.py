from movie_agent.data_utils import YouTubeCredentialDataUtils
from thirdparty.youtube_data_helper import YTManager
from .model_helper import AIModelProvider
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import json

YT_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

class YoutubeDataHelper():

    def __init__(self):
        self.yt_creds_du = YouTubeCredentialDataUtils()
        self.yt_manager = YTManager()
        self.ai_model_provider = AIModelProvider()

    def get_yt_creds(self, user):
        yt_cred = self.yt_creds_du.get_yt_credential(user=user)
        scopes = YT_SCOPES
        if yt_cred.scopes:
            try:
                scopes = json.loads(yt_cred.scopes)
            except Exception:
                scopes = [s.strip() for s in yt_cred.scopes.split(",")]

        creds = Credentials(
            token=yt_cred.access_token,
            refresh_token=yt_cred.refresh_token,
            token_uri=yt_cred.token_uri,
            client_id=yt_cred.client_id,
            client_secret=yt_cred.client_secret,
            scopes=scopes,
        )
        # Refresh if needed
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # update DB
                yt_cred.access_token = creds.token
                yt_cred.expiry = creds.expiry
                yt_cred.save(update_fields=["access_token", "expiry", "updated_at"])

        return creds

    def get_user_yt_data(self, user):
        creds = self.get_yt_creds(user)
        self.yt_manager.set_credentials(creds)
        subs = self.yt_manager.subscriptions_list()
        subs_str = ""
        for subscription in subs:
            channel_title = subscription['snippet']['title']
            channel_description = subscription['snippet']['description'][:150]
            subs_str += "\n".join(
                f"Title: {channel_title} | Description: {channel_description}")
        resp, status = self.analyse_and_extract_facts_from_data(user, subs_str)
        if not status:
            return {"code": 400, "message": resp.get('message')}, False
        return resp, True

    def analyse_and_extract_facts_from_data(self, user, data):
        prompt = f"""
            You are specially programmed for identifing user favouraible area of interest
            using users subscription data of youtube
            Here is users youtube subscription data
            {data}
            1. The user's main areas of interest.
            2. Map these interests to movie genres the user is likely to enjoy. 
            Use common movie genres like: Action, Comedy, Romance, Sci-Fi, Thriller, Drama, Horror, Fantasy, Animation, Adventure, Mystery.

            Return the output strictly in JSON with this structure:

            {{
            "interests": ["interest1", "interest2", ...],
            "movie_genres": ["genre1", "genre2", ...]
            }}
        """
        messages=[
            {"role": "system", "content": "You are a movie recommendation assistant."},
            {"role": "user", "content": prompt}
        ]
        res, status = self.ai_model_provider.get_ai_response(messages)
        if not status:
            return res, False
        return res, True
