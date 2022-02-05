"""
created matt_dumont 
on: 5/02/22
"""
import datetime
import warnings
import socket
import pandas as pd
from aw_client import ActivityWatchClient
from aw_core import Event

manual_bucket_id = f'ui-manual_{socket.gethostname()}'


def create_manual_bucket():
    """
    create the manual data bucket
    :return:
    """
    with ActivityWatchClient() as aw:
        t = aw.create_bucket(bucket_id=manual_bucket_id, event_type='manual')


def delete_manual_data(eid, force=False):
    """

    :param eid: event id
    :return:
    """
    with ActivityWatchClient() as aw:
        t = aw._delete(f"buckets/{manual_bucket_id}/events/{eid}" + ("?force=1" if force else ""))
    assert t.status_code == 200, t.text


def add_manual_data(start: datetime.datetime, duration: float, tag: str, overlap='warn'):  # todo check
    """

    :param start: datetime object will be changed to utc.
    :param duration: seconds
    :param tag: str, tag
    :param overlap: one of: "overwrite": if the new event overlaps with previous events then all events will
                                         deleted and replace with new events where the passed (new) event is kept
                                         completely and the overlapped events (old) are truncated to prevent any overlap
                                         in the database
                            "warn_overwrite": default, same as "overwrite", but warns user
                            "underwrite": if the new event overlaps with previous events it will be truncated to prevent
                                          any overlapping data. the previous events will not be impacted.
                            "warn_underwrite":  same as "underwrite", but warns user
                            "raise": raises an exception to prevent saving overlapping data.
    :return:
    """
    start = start.astimezone(datetime.timezone.utc)
    stop = start + datetime.timedelta(seconds=duration)
    assert overlap in ["overwrite", "warn_overwrite", "underwrite", "warn_underwrite", "raise"]
    events = []
    delete_events = []
    manual_data = get_manual(fromdatetime=(start - datetime.timedelta(hours=24)).isoformat(),
                             todatetime=(start + datetime.timedelta(hours=24)).isoformat())
    manual_data.loc[:, 'start_in'] = False
    idx = (manual_data.start >= start) & (manual_data.start <= stop)
    manual_data.loc[idx, 'start_in'] = True

    manual_data.loc[:, 'stop_in'] = False
    idx = (manual_data.stop >= start) & (manual_data.stop <= stop)

    overlaps = manual_data.loc[manual_data.start_in | manual_data.stop_in]

    if len(overlaps) > 0:
        if overlap in ["overwrite", "warn_overwrite"]:
            if 'warn' in overlap:
                warnings.warn('overwriting previous events')
            # add main event
            temp = Event(timestamp=start, duration=duration,
                         data=dict(tag=tag))
            events.append(temp)

            # previous events that are fully inside the new time period
            idx = overlaps.start_in & overlaps.stop_in
            delete_events.extend(overlaps.index[idx])

            # previous events, whose starts are in the time period, move start to 1s after stop
            idx = overlaps.start_in & ~overlaps.stop_in
            delete_events.extend(overlaps.index[idx])
            for r, t in overlaps.loc[idx].iterrows():
                use_start = stop + datetime.timedelta(seconds=1)
                use_duration = (t.loc['stop'] + t.loc[start] - use_start).total_seconds()
                use_tag = t.loc['tag']
                temp = Event(timestamp=use_start, duration=use_duration,
                             data=dict(tag=use_tag))
                events.append(temp)

            # previous events whose stops are in the time period, change duration to 1s before start
            idx = ~overlaps.start_in & overlaps.stop_in
            delete_events.extend(overlaps.index[idx])
            for r, t in overlaps.loc[idx].iterrows():
                use_tag = t.loc['tag']
                use_start = t.loc['start']
                use_duration = t.loc['duration'].total_seconds() - (t.loc['stop'] - start).total_seconds()
                temp = Event(timestamp=use_start, duration=use_duration,
                             data=dict(tag=use_tag))
                events.append(temp)
        elif overlap in ["underwrite", "warn_underwrite"]:
            if 'warn' in overlap:
                warnings.warn('reducing event size to prevent overlapping events')
                # todo break into multiple events if needed, sort overlaps by start time and then iterate through them?
            # todo underwrite
            raise NotImplementedError
        elif overlap == "raise":
            raise ValueError('stopped to prevent overlapping events')
        else:
            raise ValueError("should not get here")
    else:
        temp = Event(timestamp=start, duration=duration,
                     data=dict(tag=tag))
        events.append(temp)

    with ActivityWatchClient() as aw:
        for event in events:
            aw.insert_event(manual_bucket_id, event=event)
    for idv in delete_events:
        delete_manual_data(idv)


def get_manual(fromdatetime: str, todatetime: str) -> pd.DataFrame:
    """
    return manual data in utc time
    :param fromdatetime: local time zone iso format
    :param todatetime: local time zone iso format
    :return:
    """

    query = (f'manual = flood(query_bucket(find_bucket("{manual_bucket_id}")));\n' +
             'RETURN = {"events": manual};')

    # manage timezones and daylight savings time..., looks like aw logs in utc.
    fromdatetime = datetime.datetime.fromisoformat(fromdatetime).astimezone(datetime.timezone.utc)
    todatetime = datetime.datetime.fromisoformat(todatetime).astimezone(datetime.timezone.utc)

    with ActivityWatchClient() as aw:
        if manual_bucket_id not in aw.get_buckets().keys():
            raise NotImplementedError('manual bucket had not been created yet')
        data = aw.query(query, [(fromdatetime, todatetime)])

    events = [
        {
            "id": e['id'],
            "timestamp": e["timestamp"],
            "duration": datetime.timedelta(seconds=e["duration"]),
            **e["data"],
        }
        for e in data[0]["events"]
    ]

    df = pd.json_normalize(events)
    df["start"] = pd.to_datetime(df["timestamp"], infer_datetime_format=True)
    df["stop"] = df.loc[:, 'start'] + df.loc[:, 'duration']
    df.set_index("id", inplace=True)
    return df


def get_afk_data(fromdatetime: str, todatetime: str) -> pd.DataFrame:
    """
    return afk data in utc time
    :param fromdatetime: local time zone iso format
    :param todatetime: local time zone iso format
    :return:
    """
    query = """
    afk = flood(query_bucket(find_bucket("aw-watcher-afk_")));
    RETURN = {"events": afk};
    """
    # manage timezones and daylight savings time..., looks like aw logs in utc.
    fromdatetime = datetime.datetime.fromisoformat(fromdatetime).astimezone(datetime.timezone.utc)
    todatetime = datetime.datetime.fromisoformat(todatetime).astimezone(datetime.timezone.utc)

    with ActivityWatchClient() as aw:
        data = aw.query(query, [(fromdatetime, todatetime)])

    events = [
        {
            "id": e['id'],
            "timestamp": e["timestamp"],
            "duration": datetime.timedelta(seconds=e["duration"]),
            **e["data"],
        }
        for e in data[0]["events"]
    ]

    df = pd.json_normalize(events)
    df["start"] = pd.to_datetime(df["timestamp"], infer_datetime_format=True)
    df["stop"] = df.loc[:, 'start'] + df.loc[:, 'duration']
    df.set_index("id", inplace=True)
    return df


def get_window_watcher_data(fromdatetime: str, todatetime: str) -> pd.DataFrame:
    """
    return window watcher data in utc time
    :param fromdatetime: local time zone iso format
    :param todatetime: local time zone iso format
    :return:
    """

    query = """
    window = flood(query_bucket(find_bucket("aw-watcher-window_")));
    RETURN = {"events": window};
    """
    # manage timezones and daylight savings time..., looks like aw logs in utc.
    fromdatetime = datetime.datetime.fromisoformat(fromdatetime).astimezone(datetime.timezone.utc)
    todatetime = datetime.datetime.fromisoformat(todatetime).astimezone(datetime.timezone.utc)

    with ActivityWatchClient() as aw:
        data = aw.query(query, [(fromdatetime, todatetime)])

    events = [
        {
            "id": e['id'],
            "timestamp": e["timestamp"],
            "duration": datetime.timedelta(seconds=e["duration"]),
            **e["data"],
        }
        for e in data[0]["events"]
    ]

    df = pd.json_normalize(events)
    df["start"] = pd.to_datetime(df["timestamp"], infer_datetime_format=True)
    df["stop"] = df.loc[:, 'start'] + df.loc[:, 'duration']
    df.set_index("id", inplace=True)
    return df


if __name__ == '__main__':
    # delete_manual_data(342)
    t = get_afk_data('2022-02-04', '2022-02-06')
    pass
