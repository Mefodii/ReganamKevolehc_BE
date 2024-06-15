RESTRICTED_CHARS = ['<', '>', ':', '\"', '/', '\\', '?', '*', '|']
DEFAULT_REPLACE_CHAR = "_"
NON_PARSED_CHARS = [
    ["&#39;", "'"],
    ["&quot;", "'"],
    ["&amp;", "&"]
]

CHARS_VARIATIONS = (
    (("—", "‒", "–"), "-"),
    (("’", "`", "‘"), "'")
)

FILE_EXTENSION_MKV = "mkv"
FILE_EXTENSION_MP4 = "mp4"
FILE_EXTENSION_MP3 = "mp3"
FILE_EXTENSION_M4A = "m4a"
MERGED_FORMAT = FILE_EXTENSION_MKV

DEFAULT_YOUTUBE_WATCH = "https://www.youtube.com/watch?v="
ALLOWED_VIDEO_QUALITY = [720, 1080]
