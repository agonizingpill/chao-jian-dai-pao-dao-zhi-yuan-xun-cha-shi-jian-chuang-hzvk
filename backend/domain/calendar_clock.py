from datetime import datetime, timedelta, timezone

from core.records import need

UTC_PLUS_EIGHT = timezone(timedelta(hours=8))


def local_time(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=UTC_PLUS_EIGHT)
    except ValueError:
        need(False, "请使用 YYYY-MM-DD HH:MM 格式录入当地时刻")


def minutes_between(start, end):
    return int((end - start).total_seconds() // 60)
