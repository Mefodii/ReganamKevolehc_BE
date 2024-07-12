from django.db import models


class Notes(models.Model):
    # TODO: category enum
    # Usage example: when renaming a track which is already Downloaded or Inlibrary ->
    #   New note should be created with category "Track" and comment: "Rename: <old> -> <new>"
    category = models.CharField(max_length=100)
    comment = models.TextField()
    done = models.BooleanField(default=False)
