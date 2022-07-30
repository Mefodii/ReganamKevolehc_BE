from datetime import datetime

from django.db import models


class Artist(models.Model):
    name = models.CharField(max_length=300)
    monitoring = models.BooleanField(default=False)
    check_date = models.DateTimeField(default=datetime(2001, 1, 1))

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class Album(models.Model):
    name = models.CharField(max_length=300)
    published_at = models.DateTimeField(null=True, blank=True)
    artist = models.ForeignKey(Artist, related_name="album", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class Track(models.Model):
    title = models.CharField(max_length=300)
    in_playlist = models.BooleanField(default=False)
    artist = models.ForeignKey(Artist, related_name="track", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
