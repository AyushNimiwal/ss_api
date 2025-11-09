from django.db import models
from django.contrib.auth.models import User
from movie_agent.app_settings import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator

class YouTubeCredential(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="users")
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    expiry = models.DateTimeField(blank=True, null=True)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    token_uri = models.CharField(max_length=255, default="https://oauth2.googleapis.com/token")
    scopes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"YT cred for {self.user.email}"


class Content(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=1500, null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    content_type = models.IntegerField(choices=ContentType.choices, default=ContentType.MOVIE)
    imdbId = models.CharField(max_length=20, null=True, blank=True)
    tmdbId = models.CharField(max_length=20, null=True, blank=True)
    justwatchId = models.CharField(max_length=20, null=True, blank=True)
    genres = models.JSONField(default=list, blank=True)
    posterUrl = models.CharField(max_length=500, null=True, blank=True)
    backdropUrl = ArrayField(
        base_field=models.CharField(max_length=500, null=True, blank=True),
        default=list,
        blank=True,
    )

    def __str__(self):
        return self.title

class UserContent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
        related_name="content_interactions")
    content = models.ForeignKey("Content", on_delete=models.CASCADE,
        related_name="user_interactions")
    watched = models.BooleanField(default=False)
    liked = models.BooleanField(null=True)
    rating = models.IntegerField(null=True, blank=True, 
        validators=[MinValueValidator(1), MaxValueValidator(5)])
    feedback = models.TextField(null=True, blank=True)
    last_watched_at = models.DateTimeField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "content")

    def __str__(self):
        return f"{self.user} - {self.content} | watched: {self.watched}"