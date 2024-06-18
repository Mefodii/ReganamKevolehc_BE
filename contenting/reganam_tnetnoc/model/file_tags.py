from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo


class FileTags:
    AUTHOR = "AUTHOR"
    COPYRIGHT = "COPYRIGHT"
    COMMENT = "COMMENT"
    DISC = "DISC"
    EPISODE_ID = "EPISODE_ID"
    GENRE = "GENRE"
    TITLE = "TITLE"
    TRACK = "TRACK"

    @staticmethod
    def extract_from_youtubevideo(item: YoutubeVideo) -> dict:
        tags = {
            FileTags.TITLE: item.title,
            FileTags.TRACK: str(item.number),
            FileTags.COPYRIGHT: item.channel_name,
            FileTags.COMMENT: "by Mefodii"
        }
        if item.file_extension.is_audio():
            tags[FileTags.GENRE] = item.channel_name
            tags[FileTags.DISC] = item.video_id
        else:
            tags[FileTags.AUTHOR] = item.channel_name
            tags[FileTags.EPISODE_ID] = item.video_id

        return tags
