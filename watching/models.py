from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from constants.constants import MODEL_LIST_SEPARATOR
from constants.enums import WatchingType, WatchingStatus, WatchingAirStatus
from utils.model_utils import PositionedModel


class GroupManager(models.Manager):
    def filter_by_type(self, video_type):
        if video_type is None:
            return self

        return self.filter(Q(type=video_type))


class Group(models.Model):
    name = models.CharField(max_length=200)
    alias = models.CharField(max_length=1000, blank=True)  # with MODEL_LIST_SEPARATOR
    links_arr = models.CharField(max_length=3000, blank=True)  # with MODEL_LIST_SEPARATOR
    type = models.CharField(max_length=50, choices=WatchingType.as_choices())

    single = models.BooleanField()

    # NOTE: relevant fields for single = False, otherwise default value
    airing_status = models.CharField(max_length=50, choices=WatchingAirStatus.as_choices(), blank=True)
    check_date = models.DateField(default=None, blank=True, null=True)

    # NOTE: relevant fields for single = True, otherwise default value
    status = models.CharField(max_length=50, choices=WatchingStatus.as_choices(), blank=True)
    watched_date = models.DateField(default=None, blank=True, null=True)
    rating = models.IntegerField(default=None, validators=[MinValueValidator(0), MaxValueValidator(10)],
                                 blank=True, null=True)
    year = models.IntegerField(default=None, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = GroupManager()

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


class VideoManager(models.Manager):
    def filter_by_group(self, group_id: int):
        if group_id is None:
            return self

        return self.filter(Q(group__pk=group_id))


class Video(PositionedModel):
    parent_name = "group"

    name = models.CharField(max_length=200)
    comment = models.CharField(max_length=200, blank=True)
    alias = models.CharField(max_length=1000, blank=True)  # with MODEL_LIST_SEPARATOR
    links_arr = models.CharField(max_length=3000, blank=True)  # with MODEL_LIST_SEPARATOR
    year = models.IntegerField(default=None, blank=True, null=True)
    status = models.CharField(max_length=50, choices=WatchingStatus.as_choices())
    position = models.IntegerField(validators=[MinValueValidator(1)])
    episodes = models.IntegerField()
    current_episode = models.IntegerField()
    rating = models.IntegerField(default=None, validators=[MinValueValidator(0), MaxValueValidator(10)],
                                 blank=True, null=True)
    watched_date = models.DateField(default=None, blank=True, null=True)

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="videos")

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = VideoManager()

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
        return f'{self.name} - {self.comment} - {self.position}'


class ImageModel(models.Model):
    group = models.ForeignKey(Group, related_name="images", on_delete=models.CASCADE)
    # NOTE: upload to dynamic folder:
    # https://docs.djangoproject.com/en/5.0/ref/models/fields/#django.db.models.FileField.upload_to
    image = models.ImageField(upload_to="video/image/")

    def __str__(self):
        return f'{self.group.id} - {self.group.name} - {self.image.name}'
