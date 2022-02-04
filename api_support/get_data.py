"""
created matt_dumont 
on: 5/02/22
"""
import datetime
import socket
import pandas as pd
from aw_client import ActivityWatchClient

manual_bucket_id = f'ui-manual_{socket.gethostname()}'


def create_manual_bucket():
    raise NotImplementedError  # todo


def add_manual_data():
    # todo manage overwrites etc.
    raise NotImplementedError  # todo


def get_manual(fromdatetime, todatetime):
    query = """
    manual = flood(query_bucket(find_bucket("aw-manual_")));
    RETURN = {"events": manual};
    """  # todo what hapens if I have not made the bucket????
    # todo copy window watcher when done


def get_afk_data(fromdatetime, todatetime):
    query = """
    afk = flood(query_bucket(find_bucket("aw-watcher-afk_")));
    RETURN = {"events": afk};
    """
    # todo copy window watcher when done
    raise NotImplementedError


def get_window_watcher_data(fromdatetime, todatetime):
    query = """
    window = flood(query_bucket(find_bucket("aw-watcher-window_")));
    RETURN = {"events": window};
    """
    # todo manage timezones and daylight savings time..., looks like aw logs in utc.
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    td30d = datetime.timedelta(days=30)

    aw = ActivityWatchClient()
    data = aw.query(query, [(now - td30d, now)])

    events = [
        {
            "timestamp": e["timestamp"],
            "duration": datetime.timedelta(seconds=e["duration"]),
            **e["data"],
        }
        for e in data[0]["events"]
    ]

    df = pd.json_normalize(events)
    df["timestamp"] = pd.to_datetime(df["timestamp"], infer_datetime_format=True)

    # todo manage timezone and daylight savings time, looks like aw logs in utc.

    df.set_index("timestamp", inplace=True)
    return df


if __name__ == '__main__':
    get_window_watcher_data(0, 0)
