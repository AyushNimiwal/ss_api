from django.utils import timezone
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from rest_framework_simplejwt.tokens import RefreshToken
from movie_agent.data_utils import (
    YouTubeCredentialDataUtils, UserDataUtils, ContentDataUtils)
from .helper.movie_helper import MovieDataHelper
from .helper.yt_helper import YoutubeDataHelper
from movie_agent.data_utils import UserContentDataUtils
from random import sample


class GoogleAuthUtils():
    user_du = UserDataUtils()
    yt_cred_du = YouTubeCredentialDataUtils()

    def get_oauth_flow(self, redirect_uri=None, state=None):
        """Create a Google OAuth Flow object."""
        flow = Flow.from_client_config(
            settings.CLIENT_CONFIG,
            scopes=settings.SCOPES,
            state=state
        )
        flow.redirect_uri = redirect_uri or settings.YT_OAUTH_REDIRECT_URI
        return flow

    def generate_auth_url(self, redirect_uri=None, force_consent=True):
        """Generate Google OAuth URL."""
        flow = self.get_oauth_flow(redirect_uri)
        extra_params = {
            "access_type": "offline",
            "include_granted_scopes": "true",
        }
        if force_consent:
            extra_params["prompt"] = "consent"
        auth_url, state = flow.authorization_url(**extra_params)
        return auth_url, state
    
    def exchange_code_for_tokens(self, code, redirect_uri=None):
        """Exchange auth code for credentials."""
        flow = self.get_oauth_flow(redirect_uri)
        try:
            flow.fetch_token(code=code)
        except Exception as e:
            print("Error fetching token:", e)
            return None
        creds = flow.credentials
        oauth2_client = build("oauth2", "v2", credentials=creds)
        user_info = oauth2_client.userinfo().get().execute()
        user, _ = self.user_du.get_or_create_user(
            email=user_info["email"],
            defaults={"username": user_info.get("name") or user_info["email"]}
        )

        existing_creds = self.yt_cred_du.get_yt_credential(user=user)
        refresh_token = getattr(creds, "refresh_token", None)
        if not refresh_token and existing_creds:
            refresh_token = existing_creds.refresh_token


        self.yt_cred_du.update_or_create_yt_credential(
            user=user,
            defaults={
                "access_token": creds.token,
                "refresh_token": refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": ",".join(creds.scopes),
                "expiry": creds.expiry,
            }
        )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        data = {
            "user_email": user.email,
            "username": user.username,
            "access_token": access_token,
            "refresh_token": refresh_token
        }
        return {"code": 0, "data": data}, 200


class SSRecommander():
    yt_data_helper = YoutubeDataHelper()
    movie_data_helper = MovieDataHelper()
    usr_cnt_du = UserContentDataUtils()
    cnt_du = ContentDataUtils()
    google_utils = GoogleAuthUtils()

    def handle_onboarding_suggestions(self, user, **kwargs):
        limit = max(int(kwargs.get("limit", 10)), 1)
        resp, status = self.yt_data_helper.get_user_yt_data(user)
        if not status:
            return {"code": 400, "message": resp.get('message')}, 200
        usr_cnt_data = self._build_user_feedback_data(user)
        resp, status = self.movie_data_helper.get_movie_suggesstion(
            user, resp, usr_cnt_data, limit)
        if not status:
            return {"code": 400, "message": resp.get('message')}, 200
        if len(resp) == 0:
            resp, status = self.get_usr_contents(user, limit)
            if not status:
                return {"code": 400, "message": resp.get('message')}, 200
        return {"code": 0, "data": resp}, 200

    def _build_user_feedback_data(self, user):
        wtd_usr_cnts = self.usr_cnt_du.filter_user_contents(
            user=user, watched=True).order_by('-last_watched_at')[:10]
        if not wtd_usr_cnts:
            return None
        user_content_data = []
        for uc in wtd_usr_cnts:
            content = uc.content
            user_content_data.append({
                "title": content.title,
                "genres": getattr(content, "genres", []),
                "description": content.description[:200],
                "release_year": getattr(content, "release_date", None).year if content.release_date else None,
                "user_feedback": uc.feedback,
                "rating": uc.rating,
            })
        return user_content_data

    def get_usr_contents(self, user, limit, query=None, not_watched=True):
        f_dict = {
            "user_id": user.id,
        }
        if not_watched:
            f_dict["watched"] = False
        if query:
            f_dict["content__title__icontains"] = query.strip()

        qs = self.usr_cnt_du.filter_user_contents(**f_dict)
        if not qs:
            return [], True
        qs = list(qs)
        random_contents = sample(qs, min(limit, len(qs)))
        data = []
        for cnt in random_contents:
            c = cnt.content
            data.append({
                    "id": cnt.id,
                    "title": c.title,
                    "description": c.description,
                    "release_date": c.release_date.strftime("%d-%m-%Y") if c.release_date else None,
                    "content_type": c.content_type,
                    "imdbId": c.imdbId,
                    "tmdbId": c.tmdbId,
                    "liked": cnt.liked,
                    "lastWatched": cnt.last_watched_at,
                    "feedback": cnt.feedback,
                    "justwatchId": c.justwatchId,
                    "posterUrl": c.posterUrl,
                    "backdropUrl": c.backdropUrl,
                })
        return data, True

    def suggestions_by_query(self, user, **kwargs):
        query=kwargs.get("query", None)
        limit = max(int(kwargs.get("limit", 10)), 1)
        if not query or not isinstance(query, str):
            return {'code': 400, 'message': 'Invalid input provided'}, 200
        resp, status = self.yt_data_helper.get_user_yt_data(user)
        if not status:
            return {"code": 400, "message": resp.get('message')}, 200
        usr_cnt_data = self._build_user_feedback_data(user)
        resp, status = self.movie_data_helper.get_movie_suggesstion(
            user, resp, usr_cnt_data, query, limit)
        if not status:
            return {"code": 400, "message": resp.get('message')}, 200
        if len(resp) == 0:
            resp, status = self.get_usr_contents(user, limit, query, False)
            if not status:
                return {"code": 400, "message": resp.get('message')}, 200
        return {"code": 0, "data": resp}, 200

    def update_usr_cnt_feedback(self, id, **kwargs):
        is_liked = kwargs.get("is_liked", None)
        comment = kwargs.get("comment", None)
        rating = kwargs.get("rating", None)
        if comment and not isinstance(comment, str):
            return {"code": 400, "message": "Invalid Comment"}, 200
        usr_cnt = self.usr_cnt_du.get_user_content(id=id)
        if not usr_cnt:
            return {"code": 400, "message": "No such content found for you"}, 200
        usr_cnt.watched = True
        usr_cnt.feedback = comment
        if is_liked: usr_cnt.liked = is_liked
        usr_cnt.last_watched_at = timezone.now()
        usr_cnt.rating = rating
        usr_cnt.save()
        return {"code": 0, "message": "content updated successfully"}, 200


