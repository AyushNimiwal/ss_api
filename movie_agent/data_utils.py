from typing import Optional, Dict
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from movie_agent.models import YouTubeCredential, Content, UserContent


class UserDataUtils():

    def get_or_create_user(self, email, defaults=None):
        return User.objects.get_or_create(
            email=email,
            defaults=defaults or {}
        )

class YouTubeCredentialDataUtils():

    def create_yt_credentials(self, **kwargs):
        return YouTubeCredential.objects.create(**kwargs)

    def get_yt_credential(self, **kwargs):
        try:
            return YouTubeCredential.objects.get(**kwargs)
        except ObjectDoesNotExist:
            return None
        
    def update_or_create_yt_credential(self, user, defaults=None):
        return YouTubeCredential.objects.update_or_create(
            user=user,
            defaults=defaults or {}
        )
    

class ContentDataUtils:
    

    def create_content(self, **kwargs):
        return Content.objects.create(**kwargs)

    def get_content_by_id(self, content_id: int):
        try:
            return Content.objects.get(id=content_id)
        except ObjectDoesNotExist:
            return None

    def get_or_create_content(self, defaults: Optional[Dict] = None, **kwargs):
        return Content.objects.get_or_create(defaults=defaults or {}, **kwargs)

    def list_all_contents(self):
        return list(Content.objects.all())
    
    def filter_contents(self, **kwargs):
        return Content.objects.filter(**kwargs)

class UserContentDataUtils:


    def create_user_content(self, user, content, **kwargs):
        return UserContent.objects.create(user=user, content=content, **kwargs)

    def get_user_content(self, **kwargs):
        try:
            return UserContent.objects.get(**kwargs)
        except ObjectDoesNotExist:
            return None

    def update_or_create_user_content(self, user, content, 
            defaults: Optional[Dict] = None):
        return UserContent.objects.update_or_create(
            user=user,
            content=content,
            defaults=defaults or {}
        )

    def filter_user_contents(self, **kwargs):
        return UserContent.objects.filter(**kwargs)