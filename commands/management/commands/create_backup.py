import os
import datetime
import shutil
from django.core.management.base import BaseCommand

from watching.resources import GroupResource, VideoResource, ImageModelResource
from utils.File import write_file_utf8

BACKUPS_PATH = "backups\\"
MEDIA_PATH = 'media'


class Command(BaseCommand):
    def handle(self, **options):
        cwd = os.getcwd()
        self.make_backup()
        os.chdir(cwd)

    def make_backup(self):
        today = str(datetime.date.today())
        backup_dir = BACKUPS_PATH + "backup - " + today
        media_dir = os.getcwd() + "\\" + MEDIA_PATH
        os.mkdir(backup_dir)
        os.chdir(backup_dir)

        shutil.copytree(media_dir, os.getcwd() + "\\media")

        resources = [
            [GroupResource(), "Group - " + today],
            [VideoResource(), "Video - " + today],
            [ImageModelResource(), "Image - " + today],
        ]

        [self.export_resource(resource[0], resource[1]) for resource in resources]

    def export_resource(self, resource, export_name):
        dataset = resource.export()
        json_file = export_name + ".json"
        csv_file = export_name + ".csv"

        write_file_utf8(json_file, str(dataset.json))
        write_file_utf8(csv_file, str(dataset.csv))
