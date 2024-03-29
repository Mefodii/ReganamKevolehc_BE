from django.db import models
from django.db.models import Q

from django.core.validators import MaxValueValidator, MinValueValidator

from utils.constants import MODEL_LIST_SEPARATOR

WATCHIO_TYPE_ANIME = "Anime"
WATCHIO_TYPE_MOVIE = "Movie"
WATCHIO_TYPE_SERIAL = "Serial"

WATCHIO_STATUS_DROPPED = "Dropped"
WATCHIO_STATUS_PLANNED = "Planned"
WATCHIO_STATUS_IGNORED = "Ignored"
WATCHIO_STATUS_WATCHING = "Watching"
WATCHIO_STATUS_FINISHED = "Finished"

WATCHIO_AIR_STATUS_ONGOING = "Ongoing"
WATCHIO_AIR_STATUS_COMPLETED = "Completed"

WATCHIO_TYPE_CHOICES = (
    (WATCHIO_TYPE_ANIME, WATCHIO_TYPE_ANIME),
    (WATCHIO_TYPE_MOVIE, WATCHIO_TYPE_MOVIE),
    (WATCHIO_TYPE_SERIAL, WATCHIO_TYPE_SERIAL),
)

WATCHIO_STATUS_CHOICES = (
    (WATCHIO_STATUS_DROPPED, WATCHIO_STATUS_DROPPED),
    (WATCHIO_STATUS_PLANNED, WATCHIO_STATUS_PLANNED),
    (WATCHIO_STATUS_IGNORED, WATCHIO_STATUS_IGNORED),
    (WATCHIO_STATUS_WATCHING, WATCHIO_STATUS_WATCHING),
    (WATCHIO_STATUS_FINISHED, WATCHIO_STATUS_FINISHED),
)

WATCHIO_AIR_STATUS_CHOICES = (
    (WATCHIO_AIR_STATUS_ONGOING, WATCHIO_AIR_STATUS_ONGOING),
    (WATCHIO_AIR_STATUS_COMPLETED, WATCHIO_AIR_STATUS_COMPLETED),
)


class GroupQuerySet(models.QuerySet):
    def filter_by_type(self, video_type):
        if video_type is None:
            return self

        return self.filter(Q(type=video_type))


class Group(models.Model):
    name = models.CharField(max_length=200)
    alias = models.CharField(max_length=1000, blank=True)  # with MODEL_LIST_SEPARATOR
    links_arr = models.CharField(max_length=3000, blank=True)  # with MODEL_LIST_SEPARATOR
    type = models.CharField(max_length=50, choices=WATCHIO_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    check_date = models.DateField(blank=True, null=True)
    watched_date = models.DateField(blank=True, null=True)
    single = models.BooleanField(default=False)
    status = models.CharField(max_length=50, choices=WATCHIO_STATUS_CHOICES, blank=True, null=True)
    airing_status = models.CharField(max_length=50, choices=WATCHIO_AIR_STATUS_CHOICES, blank=True, null=True)
    rating = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    year = models.IntegerField(default=0)

    objects = GroupQuerySet.as_manager()

    def get_aliases(self):
        if self.alias:
            return self.alias.split(MODEL_LIST_SEPARATOR)
        return []

    def get_links(self):
        if self.links_arr:
            return self.links_arr.split(MODEL_LIST_SEPARATOR)
        return []

    @staticmethod
    def build_alias(aliases):
        return MODEL_LIST_SEPARATOR.join(aliases)

    @staticmethod
    def build_links(links):
        return MODEL_LIST_SEPARATOR.join(links)

    def __str__(self):
        return self.name


class VideoQuerySet(models.QuerySet):
    def filter_by_type(self, video_type):
        if video_type is None:
            return self

        return self.filter(Q(type=video_type))


class Video(models.Model):
    name = models.CharField(max_length=200)
    comment = models.CharField(max_length=200, blank=True)
    alias = models.CharField(max_length=1000, blank=True)  # with MODEL_LIST_SEPARATOR
    links_arr = models.CharField(max_length=3000, blank=True)  # with MODEL_LIST_SEPARATOR
    year = models.IntegerField(default=0)
    type = models.CharField(max_length=50, choices=WATCHIO_TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=WATCHIO_STATUS_CHOICES)
    order = models.IntegerField(default=1)
    episodes = models.IntegerField(default=1)
    current_episode = models.IntegerField(default=0)
    rating = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    watched_date = models.DateField(blank=True, null=True)

    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, related_name="videos")

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = VideoQuerySet.as_manager()

    def get_aliases(self):
        if self.alias:
            return self.alias.split(MODEL_LIST_SEPARATOR)
        return []

    def get_links(self):
        if self.links_arr:
            return self.links_arr.split(MODEL_LIST_SEPARATOR)
        return []

    def reorder(self, old_order, new_order):
        lte = max(old_order, new_order)
        gte = min(old_order, new_order)
        videos = Video.objects.filter(group=self.group, order__lte=lte, order__gte=gte)\
            .exclude(pk=self.pk).order_by('order')
        order_mod = -1 if old_order < new_order else 1
        for video in videos:
            video.order = video.order + order_mod
            video.save()

    def created(self):
        self.reorder(99999, self.order)

    def deleted(self):
        self.reorder(self.order, 99999)

    @staticmethod
    def build_alias(aliases):
        return MODEL_LIST_SEPARATOR.join(aliases)

    @staticmethod
    def build_links(links):
        return MODEL_LIST_SEPARATOR.join(links)

    def __str__(self):
        return f'{self.name} - {self.comment} - {self.order}'


class ImageModel(models.Model):
    group = models.ForeignKey(Group, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="video/image/")

    def __str__(self):
        return f'{self.group.id} - {self.group.name} - {self.image.name}'

