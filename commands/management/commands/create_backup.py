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

        backup_dir = self.create_backup_dir()
        backup_path = cwd + "\\" + backup_dir
        self.copy_media(backup_path)

        os.chdir(backup_dir)
        self.backup_tables()

        os.chdir(cwd)

    def backup_tables(self):
        today = str(datetime.date.today())
        resources = [
            [GroupResource(), "Group - " + today],
            [VideoResource(), "Video - " + today],
            [ImageModelResource(), "Image - " + today],
        ]

        res_len = len(resources)
        for i in range(res_len):
            resource = resources[i]
            print(f"Exporting resource {i + 1}/{res_len} - {resource[1]}")
            self.export_resource(resource[0], resource[1])

    def create_backup_dir(self):
        today = str(datetime.date.today())
        backup_dir = BACKUPS_PATH + "backup - " + today
        print(f"Creating backup folder: {backup_dir}")
        os.mkdir(backup_dir)
        return backup_dir

    def copy_media(self, backup_path):
        media_dir = os.getcwd() + "\\" + MEDIA_PATH
        shutil.copytree(media_dir, backup_path + "\\media")

    def export_resource(self, resource, export_name):
        dataset = resource.export()
        json_file = export_name + ".json"
        csv_file = export_name + ".csv"

        write_file_utf8(json_file, str(dataset.json))
        write_file_utf8(csv_file, str(dataset.csv))
