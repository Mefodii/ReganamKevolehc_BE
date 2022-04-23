from django.db import models
from django.db.models import Q

from django.core.validators import MaxValueValidator, MinValueValidator

VIDEO_TYPE_ANIME = "Anime"
VIDEO_TYPE_MOVIE = "Movie"
VIDEO_TYPE_SERIAL = "Serial"

VIDEO_STATUS_DROPPED = "Dropped"
VIDEO_STATUS_PLANNED = "Planned"
VIDEO_STATUS_IGNORED= "Ignored"
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
    (VIDEO_STATUS_IGNORED, VIDEO_STATUS_IGNORED),
    (VIDEO_STATUS_WATCHING, VIDEO_STATUS_WATCHING),
    (VIDEO_STATUS_FINISHED, VIDEO_STATUS_FINISHED),
)


class GroupQuerySet(models.QuerySet):
    def filter_by_type(self, video_type):
        if video_type is None:
            return self

        return self.filter(Q(type=video_type))


class Group(models.Model):
    name = models.CharField(max_length=200)
    # Alias name for video. Separated by string ALIAS_SEPARATOR
    alias = models.CharField(max_length=1000, blank=True)
    type = models.CharField(max_length=50, choices=VIDEO_TYPE_CHOICES, default=VIDEO_TYPE_ANIME)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    check_date = models.DateTimeField(blank=True, null=True)

    objects = GroupQuerySet.as_manager()

    def get_aliases(self):
        return self.alias.split(ALIAS_SEPARATOR)

    def set_alias(self, aliases):
        self.alias = ALIAS_SEPARATOR.join(aliases)

    def __str__(self):
        return self.name


class VideoQuerySet(models.QuerySet):
    def filter_by_type(self, video_type):
        if video_type is None:
            return self

        return self.filter(Q(type=video_type))


class Video(models.Model):
    name = models.CharField(max_length=200)
    # Alias name for video. Separated by string ALIAS_SEPARATOR
    alias = models.CharField(max_length=1000, blank=True)
    year = models.IntegerField(default=1)
    type = models.CharField(max_length=50, choices=VIDEO_TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=VIDEO_STATUS_CHOICES, default=VIDEO_STATUS_FINISHED)
    order = models.IntegerField(default=1)
    episodes = models.IntegerField(default=1)
    rating = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])

    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, related_name="videos")

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = VideoQuerySet.as_manager()

    def get_aliases(self):
        return self.alias.split(ALIAS_SEPARATOR)

    def set_alias(self, aliases):
        self.alias = ALIAS_SEPARATOR.join(aliases)

    def __str__(self):
        return self.name


class ImageModel(models.Model):
    group = models.ForeignKey(Group, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="video/image/")

