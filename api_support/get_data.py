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
import numpy as np

manual_bucket_id = f'ui-manual_{socket.gethostname()}'


def create_manual_bucket():
    """
    create the manual data bucket
    :return:
    """
    with ActivityWatchClient() as aw:
        t = aw.create_bucket(bucket_id=manual_bucket_id, event_type='manual')


def delete_manual_data(eid: int, force=False):
    """

    :param eid: event id
    :return:
    """
    with ActivityWatchClient() as aw:
        t = aw._delete(f"buckets/{manual_bucket_id}/events/{eid}" + ("?force=1" if force else ""))
    assert t.status_code == 200, t.text


def add_manual_data(start: datetime.datetime, duration: float, tag: str, overlap='overwrite',
                    exclude_afk_time=False):
    """

    :param start: datetime object utc.
    :param duration: seconds
    :param tag: str, tag
    :param overlap: one of: "overwrite": if the new event overlaps with previous events then all events will
                                         deleted and replace with new events where the passed (new) event is kept
                                         completely and the overlapped events (old) are truncated to prevent any overlap
                                         in the database
                            "underwrite": if the new event overlaps with previous events it will be truncated to prevent
                                          any overlapping data. the previous events will not be impacted.
                            "raise": raises an exception to prevent saving overlapping data.
    :param exclude_afk_time: bool if True only add the tag to time that is not afk # todo not implmented
    :return:
    """
    if exclude_afk_time:
        raise NotImplementedError  # todo
    stop = start + datetime.timedelta(seconds=duration)
    assert overlap in ["overwrite", "underwrite", "raise", 'delete']
    events = []
    delete_events = []
    manual_data = get_manual(fromdatetime=(start - datetime.timedelta(hours=24)).isoformat(),
                             todatetime=(start + datetime.timedelta(hours=24)).isoformat())
    if manual_data is not None:
        manual_data.loc[:, 'overlapping'] = False
        idx = (manual_data.start <= start) & (manual_data.stop >= stop)  # existing in the middle of new
        manual_data.loc[idx, 'overlapping'] = True
        idx = (manual_data.stop <= stop) & (manual_data.stop > start)  # left overhanging and middle
        manual_data.loc[idx, 'overlapping'] = True
        idx = (manual_data.start >= start) & (manual_data.start <= stop)  # right overhanging middle
        manual_data.loc[idx, 'overlapping'] = True
        idx = (manual_data.start <= start) & (manual_data.stop >= stop)  # new in middle of existing
        manual_data.loc[idx, 'overlapping'] = True

        overlaps = manual_data.loc[manual_data.loc[:, 'overlapping']]

        if len(overlaps) > 0:
            if overlap == 'delete':
                delete_events.extend(overlaps.index)
            elif overlap in ["overwrite"]:
                # add main event
                temp = Event(timestamp=start, duration=duration,
                             data=dict(tag=tag))
                events.append(temp)

                # previous events that are fully inside the new time period
                idx = (overlaps.start > start) & (overlaps.stop < stop)
                delete_events.extend(overlaps.index[idx])

                # previous events, whose starts are in the time period, move start to 1s after stop
                idx = (overlaps.start >= start) & (overlaps.stop > stop)
                delete_events.extend(overlaps.index[idx])
                for r, t in overlaps.loc[idx].iterrows():
                    use_start = stop + datetime.timedelta(seconds=1)
                    use_duration = (t.loc['stop'] - use_start).total_seconds()
                    assert use_duration > 0
                    use_tag = t.loc['tag']
                    temp = Event(timestamp=use_start, duration=use_duration,
                                 data=dict(tag=use_tag))
                    events.append(temp)

                # previous events whose stops are in the time period, change duration to 1s before start
                idx = (overlaps.stop >= start) & (overlaps.start < start)
                delete_events.extend(overlaps.index[idx])
                for r, t in overlaps.loc[idx].iterrows():
                    use_tag = t.loc['tag']
                    use_start = t.loc['start']
                    use_duration = t.loc['duration'].total_seconds() - (t.loc['stop'] - start).total_seconds()
                    assert use_duration > 0
                    temp = Event(timestamp=use_start, duration=use_duration,
                                 data=dict(tag=use_tag))
                    events.append(temp)

                idx = (overlaps.stop >= stop) & (overlaps.start < start)  # piece in middle
                for r, t in overlaps.loc[idx].iterrows():
                    use_tag = t.loc['tag']
                    use_start = stop
                    use_duration = (t.loc['stop'] - use_start).total_seconds()
                    assert use_duration > 0, f'{use_tag}, {use_start}, {use_duration}'
                    temp = Event(timestamp=use_start, duration=use_duration,
                                 data=dict(tag=use_tag))
                    events.append(temp)

            elif overlap in ["underwrite"]:
                start_ts = start.timestamp()
                stop_ts = start_ts + duration
                overlaps = overlaps.sort_values('start_unix')
                overlaps.loc[:, 'next_start'] = overlaps.loc[:, 'start_unix'].shift(-1)
                overlaps.loc[:, 'next_stop'] = overlaps.loc[:, 'stop_unix'].shift(-1)
                overlaps.loc[:, 'prev_start'] = overlaps.loc[:, 'start_unix'].shift(1)
                overlaps.loc[:, 'prev_stop'] = overlaps.loc[:, 'stop_unix'].shift(1)
                use_vals = [
                    'prev_start', 'prev_stop',
                    'start_unix', 'stop_unix',
                    'next_start', 'next_stop',
                ]
                use_starts = []
                use_stops = []
                for vals in overlaps.loc[:, use_vals].itertuples(False, None):
                    prev_start, prev_stop, start_lap, stop_lap, next_start, next_stop = vals

                    if pd.isnull(prev_start):  # first one
                        if start_ts <= start_lap:  # first is left overhanging
                            use_start = start_ts
                            use_stop = start_lap
                            use_starts.append(use_start)
                            use_stops.append(use_stop)
                        elif start_lap < start_ts and stop_ts < stop_lap:
                            pass

                        elif start_ts <= stop_lap:  # first is right overhanging, only one value by default
                            if pd.isnull(next_start):
                                use_start = stop_lap
                                use_stop = stop_ts
                                use_starts.append(use_start)
                                use_stops.append(use_stop)
                        else:  # first is middle value
                            raise ValueError('shouldnt be able to get here')

                    elif pd.isnull(next_start):  # last one
                        use_start = prev_stop
                        use_stop = start_lap
                        use_starts.append(use_start)
                        use_stops.append(use_stop)

                        if not stop_ts <= stop_lap:  # not right overhanging, must add another overlap
                            use_start = stop_lap
                            use_stop = stop_ts
                            use_starts.append(use_start)
                            use_stops.append(use_stop)

                    else:  # middle values
                        use_start = prev_stop
                        use_stop = start_lap
                        use_starts.append(use_start)
                        use_stops.append(use_stop)

                for st, sp in zip(use_starts, use_stops):
                    use_duration = sp - st
                    assert use_duration > 0, f'{st}, {sp}, {use_duration}'
                    temp = Event(timestamp=datetime.datetime.fromtimestamp(st, datetime.timezone.utc),
                                 duration=use_duration,
                                 data=dict(tag=tag))
                    events.append(temp)
            elif overlap == "raise":
                raise ValueError('stopped to prevent overlapping events')
            else:
                raise ValueError("should not get here")
        elif overlap == 'delete':
            pass
        else:
            temp = Event(timestamp=start, duration=duration,
                         data=dict(tag=tag))
            events.append(temp)
    else:
        if overlap != 'delete':
            temp = Event(timestamp=start, duration=duration,
                         data=dict(tag=tag))
            events.append(temp)

    with ActivityWatchClient() as aw:
        for event in events:
            aw.insert_event(manual_bucket_id, event=event)
    for idv in pd.unique(delete_events):
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
        t = aw.get_events(manual_bucket_id, start=fromdatetime, end=todatetime)
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
    if df.empty:
        return None
    df["start"] = pd.to_datetime(df["timestamp"], infer_datetime_format=True)
    df["stop"] = df.loc[:, 'start'] + df.loc[:, 'duration']
    df.set_index("id", inplace=True)

    df.loc[:, 'start_unix'] = [e.timestamp() for e in df.loc[:, 'start']]
    df.loc[:, 'stop_unix'] = [e.timestamp() for e in df.loc[:, 'stop']]

    temp = (df.loc[:, 'stop_unix'] - df.loc[:, 'start_unix']) / 60
    df.loc[:, 'duration_min'] = temp

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
    if df.empty:
        return None
    df["start"] = pd.to_datetime(df["timestamp"], infer_datetime_format=True)
    df["stop"] = df.loc[:, 'start'] + df.loc[:, 'duration']
    df.set_index("id", inplace=True)

    df.loc[:, 'start_unix'] = [e.timestamp() for e in df.loc[:, 'start']]
    df.loc[:, 'stop_unix'] = [e.timestamp() for e in df.loc[:, 'stop']]

    temp = (df.loc[:, 'stop_unix'] - df.loc[:, 'start_unix']) / 60
    df.loc[:, 'duration_min'] = temp
    return df


def get_total_untagged_not_afk_data(afk_data, manual_data):
    """
    return seconds of untagged notafk time
    :param afk_data: akf data
    :param manual_data: manual data
    :return: seconds of time not in a manual tag and not afk
    """
    print(afk_data)
    print(manual_data)
    all_data = pd.DataFrame(
        index=pd.date_range(min(afk_data.start.min(), manual_data.start.min()),
                            max(afk_data.stop.max(), manual_data.stop.max()),
                            freq='T'),  # T is minutely
        columns=['not_afk', 'manual'])
    all_data.loc[:, 'not_afk'] = False
    all_data.loc[:, 'manual'] = False

    afk_data = afk_data.loc[afk_data.status != 'afk']
    for astart, astop in afk_data.loc[:, ['start', 'stop']].itertuples(False, None):
        astart = astart.round('T')
        astop = astop.round('T')
        all_data.loc[astart:astop, 'not_afk'] = True
    for mstart, mstop in manual_data.loc[:, ['start', 'stop']].itertuples(False, None):
        mstart = mstart.round('T')
        mstop = mstop.round('T')
        all_data.loc[mstart:mstop, 'manual'] = True
    total = (all_data.not_afk & ~all_data.manual).sum() * 60
    return total


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
    if df.empty:
        return None
    df["start"] = pd.to_datetime(df["timestamp"], infer_datetime_format=True)
    df["stop"] = df.loc[:, 'start'] + df.loc[:, 'duration']
    df.set_index("id", inplace=True)

    df.loc[:, 'start_unix'] = [e.timestamp() for e in df.loc[:, 'start']]
    df.loc[:, 'stop_unix'] = [e.timestamp() for e in df.loc[:, 'stop']]

    temp = (df.loc[:, 'stop_unix'] - df.loc[:, 'start_unix']) / 60
    df.loc[:, 'duration_min'] = temp

    return df


def get_labels_from_unix(unix, afk_data, ww_data, manual):
    tag = ''
    tag_dur = 0
    afk = ''
    afk_dur = 0
    cur_app = ''
    window = ''
    ww_dur = 0
    if afk_data is not None:
        if unix < afk_data.start_unix.min() or unix > afk_data.stop_unix.max():
            pass
        else:
            idx = (unix <= afk_data.stop_unix) & (unix >= afk_data.start_unix)
            if idx.sum() > 0:
                afk, afk_dur = afk_data.loc[idx, ['status', 'duration_min']].iloc[0]  # should only be one
    if manual is not None:
        if unix < manual.start_unix.min() or unix > manual.stop_unix.max():
            pass
        else:
            idx = (unix <= manual.stop_unix) & (unix >= manual.start_unix)
            if idx.sum() > 0:
                tag, tag_dur = manual.loc[idx, ['tag', 'duration_min']].iloc[0]  # should only be one
    if ww_data is not None:
        if unix < ww_data.start_unix.min() or unix > ww_data.stop_unix.max():
            pass
        else:
            idx = (unix <= ww_data.stop_unix) & (unix >= ww_data.start_unix)
            if idx.sum() > 0:
                window, cur_app, ww_dur = ww_data.loc[idx, [
                    'title', 'app', 'duration_min']].iloc[0]  # should only be one

    return tag, tag_dur, afk, afk_dur, cur_app, window, ww_dur


create_manual_bucket()

if __name__ == '__main__':
    # delete_manual_data(342)
    start = datetime.datetime.today()
    pass
