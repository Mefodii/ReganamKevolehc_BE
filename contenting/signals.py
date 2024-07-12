from time import sleep

from django.db.models.signals import pre_save, pre_delete, post_delete
from django.dispatch import receiver

from constants.enums import ContentCategory
from listening.models import Track
from .models import ContentTrack, ContentList


@receiver(post_delete, sender=ContentList)
def handle_content_watcher_deletion(sender, instance: ContentList, **kwargs):
    # Note: when deleting a list and pre_delete is called for ContentTrack, there is some concurrency on DB operations
    #   and if same track is assigned to multiple ContentTrack wich are going to be deleted, then there is a chance that
    #   the dead track will not be deleted.
    if instance.category == ContentCategory.MUSIC.value:
        sleep(3)
        Track.clean_dead()


@receiver(pre_delete, sender=ContentTrack)
def handle_content_track_deletion(sender, instance, **kwargs):
    """
    Signal handler that is called after a ContentTrack instance is deleted.
    If the associated Track is not clean and is only related to this deleted ContentTrack,
    then delete the Track as well.
    """
    track: Track | None = instance.track
    if track and not track.is_clean and track.content_tracks.count() == 1:
        track.delete()


@receiver(pre_save, sender=ContentTrack)
def handle_content_track_update(sender, instance, **kwargs):
    """
    Signal handler that is called before a ContentTrack instance is saved.
    If the track field is changed and the old track is not clean and
    is only related to this instance, then delete the old track.
    """
    if not instance.pk:
        # The instance is new, so no track change has happened
        return

    try:
        old_instance = ContentTrack.objects.get(pk=instance.pk)
    except ContentTrack.DoesNotExist:
        return

    old_track: Track | None = old_instance.track
    new_track: Track | None = instance.track

    if old_track != new_track:
        if old_track and not old_track.is_clean and old_track.content_tracks.count() == 1:
            old_track.delete()
