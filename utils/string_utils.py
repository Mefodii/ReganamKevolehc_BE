import re

from constants.constants import NON_PARSED_CHARS, RESTRICTED_CHARS, DEFAULT_REPLACE_CHAR, CHARS_VARIATIONS


def replace_unicode_chars(value: str) -> str:
    """
    Replace unicode characters in string with string characters.
    @param value:
    @return:
    """
    processed_title = value
    for chars in NON_PARSED_CHARS:
        processed_title = processed_title.replace(chars[0], chars[1])

    return processed_title


def normalize_file_name(value: str, replace_char: str = DEFAULT_REPLACE_CHAR) -> str:
    """
    Replace all restricted characters in a file name with replace_char
    @param value:
    @param replace_char:
    @return:
    """
    if replace_char in NON_PARSED_CHARS:
        raise ValueError(f"Char: {replace_char} is not supported.")

    return re.sub('[' + re.escape(''.join(RESTRICTED_CHARS)) + ']',
                  replace_char, value)


def replace_chars_variations(value: str) -> str:
    """
    Replace similar characters in a file name with its default representation.
    E.g: ("—", "‒", "–") -> "-" [Differnt variations of dash]
    @param value:
    @return:
    """
    result = value
    for chars_variation in CHARS_VARIATIONS:
        before = chars_variation[0]
        after = chars_variation[1]
        result = re.sub('[' + re.escape(''.join(before)) + ']', after, result)
    return result


def normalize_text(value: str) -> str:
    """
    Replace all special unicode chars and char variations
    @param value:
    @return:
    """
    new_text = replace_unicode_chars(value)
    return replace_chars_variations(new_text)


def is_bool_repr(value: str) -> bool:
    return value.lower() in ('true', 'false')
