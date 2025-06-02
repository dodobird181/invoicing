from datetime import datetime

import pytz

from settings import config

app_tz = pytz.timezone(config["timezone"])

"""
Some date and datetime utility functions.
"""


def pretty_datetime(dt: datetime) -> str:
    return dt.strftime("%B %-d, %Y - %-I:%M:%S %p, %Z")


def pretty_date(dt: datetime) -> str:
    return dt.strftime("%B %-d, %Y")


def filename_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d_%I:%M:%S_%p_%Z")


def app_now() -> datetime:
    """
    Local timezone now for the app.
    """
    return datetime.now(tz=app_tz)
