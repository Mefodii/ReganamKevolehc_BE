from datetime import datetime


def yt_to_py(yt_datetime):
    if "." not in yt_datetime:
        yt_datetime = yt_datetime[:-1] + ".0Z"
    return datetime.strptime(yt_datetime, '%Y-%m-%dT%H:%M:%S.%fZ')


def compare_yt_dates(d1, d2):
    py_d1 = yt_to_py(d1)
    py_d2 = yt_to_py(d2)

    if py_d1 > py_d2:
        return 1
    if py_d1 < py_d2:
        return -1

    return 0


def py_to_yt(py_datetime):
    s = py_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')
    return s[:-3]+"Z"


def get_default_ytdate():
    t = datetime(1970, 1, 1)
    return py_to_yt(t)


def get_current_ytdate():
    return py_to_yt(datetime.utcnow())
