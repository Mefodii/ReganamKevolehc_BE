from datetime import datetime, timedelta
from dateutil import parser

import pytz


def yt_to_py(yt_datetime: str) -> datetime:
    """
    Converts a datetime object to a python datetime object. \n
    Assumes yt_datetime is UTC timezone.
    @param yt_datetime:
    @return:
    """
    if "Z" not in yt_datetime:
        raise ValueError(f"yt_datetime must be UTC timezone. Received: {yt_datetime}")

    if "." not in yt_datetime:
        yt_datetime = yt_datetime[:-1] + ".0Z"
    # Note: using strptime does not add tzinfo on the datetime object
    # res = datetime.strptime(yt_datetime, '%Y-%m-%dT%H:%M:%S.%fZ')
    res = parser.parse(yt_datetime)
    return res


def compare_yt_dates(d1: str, d2: str) -> int:
    """

    :param d1:
    :param d2:
    :return: 1 if 1st > 2nd, -1 if 1st < 2nd, 0 if 1st == 2nd
    """
    py_d1 = yt_to_py(d1)
    py_d2 = yt_to_py(d2)

    if py_d1 > py_d2:
        return 1
    if py_d1 < py_d2:
        return -1

    return 0


def yt_date_diff(d1, d2) -> timedelta:
    py_d1 = yt_to_py(d1)
    py_d2 = yt_to_py(d2)

    if py_d1 > py_d2:
        return py_d1 - py_d2

    return py_d2 - py_d1


def yt_hours_diff(d1, d2) -> float:
    """
    Returns the difference in hours between two datetime objects.
    Assumes yt_datetime is UTC timezone.
    @param d1:
    @param d2:
    @return:
    """
    diff = yt_date_diff(d1, d2)
    return divmod(diff.total_seconds(), 3600)[0]


def py_to_yt(py_datetime) -> str:
    s = py_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')
    return s[:-3]+"Z"


def get_default_ytdate() -> str:
    t = datetime(1970, 1, 1)
    return py_to_yt(t)


def get_current_ytdate() -> str:
    return py_to_yt(datetime.utcnow())
