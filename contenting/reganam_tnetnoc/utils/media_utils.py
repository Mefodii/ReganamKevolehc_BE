from constants.enums import FileExtension
from contenting.reganam_tnetnoc.model.file_tags import FileTags
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo, YoutubeVideoList
from utils import file
from utils.ffmpeg import Ffmpeg
from utils.file import File


def sync_media_filenames_with_db(db_file: str, media_paths: list[str], extension: FileExtension):
    """
    For each media file in list of paths, extract video ID of the file from file's metadata.

    If file's number is different from video's number in db, then filename and metadata will be updated.
    :param db_file:
    :param media_paths:
    :param extension:
    :return:
    """
    videos_list = YoutubeVideoList.from_file(db_file)

    files = [f for path in media_paths for f in file.list_files(path)]
    media_files = filter_media_files(files, extension)

    for element in media_files:
        file_abs_path = element.get_abs_path()
        tags = Ffmpeg.read_metadata(file_abs_path)
        file_id = tags.get(FileTags.DISC) if extension.is_audio() else tags.get(FileTags.EPISODE_ID)
        if file_id is None:
            raise ValueError(f"File has no ID: {file_abs_path}")

        video = videos_list.get_by_id(file_id)
        if video is None:
            raise ValueError(f"File not found in DB: {file_abs_path}")

        expected_tags = FileTags.extract_from_youtubevideo(video)
        diff = []
        for k, expected_value in expected_tags.items():
            media_value = tags.get(k, None)
            if tags.get(k) is None:
                diff.append(f"Missing tag: {k}")

            if media_value != expected_value:
                diff.append(f"Tag mismatch value. Tag: {k}. Expected: {expected_value}. Actual: {media_value}")

        changed = False
        if len(diff) > 0:
            print(f"Mismatch of tags for video: {video}")
            [print(d) for d in diff]
            print(f"Setting new tags: {expected_tags}")
            Ffmpeg.add_tags(file_abs_path, expected_tags, loglevel="error")
            changed = True

        if video.file_name != element.get_plain_name():
            new_name = f"{video.file_name}.{extension.value}"
            print(f"Renaming: {element.get_plain_name()}. New name: {video.file_name}")
            element.rename(new_name)
            changed = True

        if changed:
            print("----")


def check_validity(db_file: str, media_paths: list[str]) -> bool:
    """
    Check that all items in db have the same number in playlist file.

    Check that all items in db with status "DOWNLOADED" have a file
    :param db_file:
    :param media_paths:
    :return:
    """

    def exists(path: str, v: YoutubeVideo) -> bool:
        abs_file_name = f"{path}\\{v.file_name}.{v.file_extension.value}"
        return file.exists(abs_file_name)

    videos = YoutubeVideoList.from_file(db_file).videos

    valid = True
    for video in videos:
        if video.status != YoutubeVideo.STATUS_DOWNLOADED:
            continue

        found = any(exists(madia_path, video) for madia_path in media_paths)
        if not found:
            valid = False
            print(f"File not found: {video.file_name}. Video ID: {video.video_id}")

    return valid


def filter_media_files(files: list[File], extension: FileExtension) -> list[File]:
    return list(filter(lambda f: f.extension == extension.value, files))
