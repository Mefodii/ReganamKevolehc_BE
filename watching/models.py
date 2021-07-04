from django.db import models
from django.db.models import Q

from django.core.validators import MaxValueValidator, MinValueValidator

VIDEO_TYPE_ANIME = "Anime"
VIDEO_TYPE_MOVIE = "Movie"
VIDEO_TYPE_SERIAL = "Serial"

VIDEO_STATUS_DROPPED = "Dropped"
VIDEO_STATUS_PLANNED = "Planned"
VIDEO_STATUS_ON_HOLD = "On Hold"
VIDEO_STATUS_WATCHING = "Watching"
VIDEO_STATUS_FINISHED = "Finished"

ALIAS_SEPARATOR = ">;<"

VIDEO_TYPE_CHOICES = (
    (VIDEO_TYPE_ANIME, VIDEO_TYPE_ANIME),
    (VIDEO_TYPE_MOVIE, VIDEO_TYPE_MOVIE),
    (VIDEO_TYPE_SERIAL, VIDEO_TYPE_SERIAL),
)

VIDEO_STATUS_CHOICES = (
    (VIDEO_STATUS_DROPPED, VIDEO_STATUS_DROPPED),
    (VIDEO_STATUS_PLANNED, VIDEO_STATUS_PLANNED),
    (VIDEO_STATUS_ON_HOLD, VIDEO_STATUS_ON_HOLD),
    (VIDEO_STATUS_WATCHING, VIDEO_STATUS_WATCHING),
    (VIDEO_STATUS_FINISHED, VIDEO_STATUS_FINISHED),
)


class VideoQuerySet(models.QuerySet):
    def filter_by_type(self, video_type):
        if video_type is None:
            return self.filter(Q(parent_video=None))

        return self.filter(
            Q(type=video_type) & Q(parent_video=None)
        )

    def movies(self):
        return self.filter_by_type(VIDEO_TYPE_MOVIE)

    def anime(self):
        return self.filter_by_type(VIDEO_TYPE_ANIME)

    def serials(self):
        return self.filter_by_type(VIDEO_TYPE_SERIAL)


class Video(models.Model):
    name = models.CharField(max_length=150)
    # Alias name for video. Separated by string ">;<"
    alias = models.CharField(max_length=800, blank=True)
    year = models.IntegerField(blank=True)
    type = models.CharField(max_length=50, choices=VIDEO_TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=VIDEO_STATUS_CHOICES, default=VIDEO_STATUS_FINISHED)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    check_date = models.DateTimeField(blank=True, null=True)
    parent_video = models.ForeignKey("self", on_delete=models.CASCADE, null=True, related_name="side_story")

    objects = VideoQuerySet.as_manager()

    def __str__(self):
        return self.name


class Season(models.Model):
    video = models.ForeignKey(Video, related_name="seasons", on_delete=models.CASCADE)
    rating = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    season_number = models.IntegerField(default=1)
    episode_number = models.IntegerField(default=1)
    current_episode = models.IntegerField(default=0)
    watched = models.BooleanField(default=False)
    watched_at = models.DateField()


class ImageModel(models.Model):
    video = models.ForeignKey(Video, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="video/image/")

