from datetime import datetime

from django.db import models

from utils.string_utils import normalize_text

ALIAS_SEPARATOR = ">{;}<"
ARTIST_SEPARATOR = ", "
FEAT_SEPARATOR = ", "


class Artist(models.Model):
    name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200, blank=True, null=True)
    alias = models.CharField(max_length=500, blank=True)
    monitoring = models.BooleanField(default=False)
    check_date = models.DateTimeField(default=datetime(2001, 1, 1))
    releasing = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.name = normalize_text(self.name)
        self.display_name = normalize_text(self.display_name)
        self.alias = normalize_text(self.alias)
        super().save(args, kwargs)

    def get_displayable_name(self):
        if self.display_name:
            return f"{self.name} ({self.display_name})"

    def get_aliases(self):
        if self.alias:
            return self.alias.split(ALIAS_SEPARATOR)
        return []

    @staticmethod
    def build_alias(aliases):
        return ALIAS_SEPARATOR.join(aliases)


class Release(models.Model):
    name = models.CharField(max_length=300)
    display_name = models.CharField(max_length=300, blank=True, null=True)
    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.name = normalize_text(self.name)
        self.display_name = normalize_text(self.display_name)
        super().save(args, kwargs)

    def get_displayable_name(self):
        if self.display_name:
            return f"{self.name} ({self.display_name})"


class Track(models.Model):
    title = models.CharField(max_length=200)
    display_title = models.CharField(max_length=200, blank=True, null=True)
    alias = models.CharField(max_length=500, blank=True)
    artists = models.ManyToManyField(Artist, related_name="tracks")
    releases = models.ManyToManyField(Release, related_name="tracks")
    feat = models.ManyToManyField(Artist, related_name="feats")
    remix = models.ManyToManyField(Artist, related_name="remixes")
    like = models.BooleanField(blank=True, null=True)
    downloaded = models.BooleanField(default=False)
    is_clean = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.title = normalize_text(self.title)
        self.display_title = normalize_text(self.display_title)
        self.alias = normalize_text(self.alias)
        super().save(args, kwargs)

    def get_displayable_title(self):
        if self.display_title:
            return f"{self.title} ({self.display_title})"

    def get_fulltitle(self) -> str:
        fulltitle = self.get_displayable_title()
        if self.feat:
            feat: Artist
            feats = FEAT_SEPARATOR.join([feat.get_displayable_name() for feat in self.feat.all()])
            fulltitle += f"[Feat. {feats}]"
        if self.remix:
            remix: Artist
            remixes = FEAT_SEPARATOR.join([remix.get_displayable_name() for remix in self.remix.all()])
            fulltitle += f"({remixes} Remix)"

        return fulltitle

    def get_fullname(self) -> str:
        artist: Artist
        fullname = ARTIST_SEPARATOR.join([artist.get_displayable_name() for artist in self.artists.all()])
        fullname += f" - {self.get_fulltitle()}"
        return fullname

    def get_aliases(self):
        if self.alias:
            return self.alias.split(ALIAS_SEPARATOR)
        return []

    @staticmethod
    def build_alias(aliases):
        return ALIAS_SEPARATOR.join(aliases)
