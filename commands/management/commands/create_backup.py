import datetime
import os
import shutil

from django.core.management.base import BaseCommand

from utils import file
from watching.resources import GroupResource, VideoResource, ImageModelResource

BACKUPS_PATH = "backups\\"
MEDIA_PATH = 'media'


def create_backup_dir():
    today = str(datetime.date.today())
    backup_dir = BACKUPS_PATH + "backup - " + today
    print(f"Creating backup folder: {backup_dir}")
    os.mkdir(backup_dir)
    return backup_dir


def copy_media(backup_path):
    media_dir = os.getcwd() + "\\" + MEDIA_PATH
    shutil.copytree(media_dir, backup_path + "\\media")


def export_resource(resource, export_name):
    dataset = resource.export()
    json_file = export_name + ".json"
    csv_file = export_name + ".csv"

    file.write(json_file, [str(dataset.json)], encoding=file.ENCODING_UTF8)
    file.write(csv_file, [str(dataset.csv)], encoding=file.ENCODING_UTF8)


def backup_tables():
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
        export_resource(resource[0], resource[1])


class Command(BaseCommand):
    def handle(self, **options):
        cwd = os.getcwd()

        backup_dir = create_backup_dir()
        backup_path = cwd + "\\" + backup_dir
        copy_media(backup_path)

        os.chdir(backup_dir)
        backup_tables()
        os.chdir(cwd)
