from django.core.management.base import BaseCommand

from watching.models import Video


class Command(BaseCommand):
    def handle(self, **options):
        videos = Video.objects.all()
        for v in videos:
            if v.group is None:
                print(v)
