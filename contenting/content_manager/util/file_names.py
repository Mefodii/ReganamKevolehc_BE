import re
from .constants import NON_PARSED_CHARS, RESTRICTED_CHARS, DEFAULT_REPLACE_CHAR


def replace_unicode_chars(video_title):
    processed_title = video_title
    for chars in NON_PARSED_CHARS:
        processed_title = processed_title.replace(chars[0], chars[1])

    return processed_title


def replace_restricted_file_chars(video_title):
    return re.sub('[' + re.escape(''.join(RESTRICTED_CHARS)) + ']',
                  DEFAULT_REPLACE_CHAR, video_title)