from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from constants.constants import MODEL_LIST_SEPARATOR
from constants.model_choices import WATCHING_TYPE_CHOICES, WATCHING_STATUS_CHOICES, WATCHING_AIR_STATUS_CHOICES
from utils.model_utils import reorder


class GroupManager(models.Manager):
    def filter_by_type(self, video_type):
        if video_type is None:
            return self

        return self.filter(Q(type=video_type))


class Group(models.Model):
    name = models.CharField(max_length=200)
    alias = models.CharField(max_length=1000, blank=True)  # with MODEL_LIST_SEPARATOR
    links_arr = models.CharField(max_length=3000, blank=True)  # with MODEL_LIST_SEPARATOR
    type = models.CharField(max_length=50, choices=WATCHING_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    check_date = models.DateField(blank=True, null=True)
    watched_date = models.DateField(blank=True, null=True)
    single = models.BooleanField(default=False)
    status = models.CharField(max_length=50, choices=WATCHING_STATUS_CHOICES, blank=True, null=True)
    airing_status = models.CharField(max_length=50, choices=WATCHING_AIR_STATUS_CHOICES, blank=True, null=True)
    rating = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)],
                                 blank=True, null=True)
    year = models.IntegerField(default=0, blank=True, null=True)

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


class Video(models.Model):
    name = models.CharField(max_length=200)
    comment = models.CharField(max_length=200, blank=True)
    alias = models.CharField(max_length=1000, blank=True)  # with MODEL_LIST_SEPARATOR
    links_arr = models.CharField(max_length=3000, blank=True)  # with MODEL_LIST_SEPARATOR
    year = models.IntegerField(default=0)
    type = models.CharField(max_length=50, choices=WATCHING_TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=WATCHING_STATUS_CHOICES)
    order = models.IntegerField(default=1)
    episodes = models.IntegerField(default=1)
    current_episode = models.IntegerField(default=0)
    rating = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    watched_date = models.DateField(blank=True, null=True)

    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, related_name="videos")

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

    def reorder(self, old_order, new_order):
        reorder(self, old_order, new_order, "order", "group")

    def updated(self, old_order):
        if self.order != old_order:
            self.reorder(old_order, self.order)

    def created(self):
        # Shift up by 1 all videos with order >= self.order
        self.reorder(None, self.order)

    def deleted(self):
        # Shift up by -1 all videos with order >= self.order
        self.reorder(self.order, None)

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
    # NOTE: upload to dynamic folder
    image = models.ImageField(upload_to="video/image/")

    def __str__(self):
        return f'{self.group.id} - {self.group.name} - {self.image.name}'
