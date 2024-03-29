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


class AwDataAccess(object):
    manual_bucket_id = f'ui-manual_{socket.gethostname()}'

    def __init__(self, client_name):
        self.client_name = client_name
        self.create_manual_bucket()

    def create_manual_bucket(self):
        """
        create the manual data bucket
        :return:
        """
        with ActivityWatchClient(client_name=self.client_name) as aw:
            if not self.manual_bucket_id in aw.get_buckets():
                t = aw.create_bucket(bucket_id=self.manual_bucket_id, event_type='manual')
        pass

    def delete_manual_data(self, eid: int, force=False):
        """

        :param eid: event id
        :return:
        """
        with ActivityWatchClient(client_name=self.client_name) as aw:
            t = aw._delete(f"buckets/{self.manual_bucket_id}/events/{eid}" + ("?force=1" if force else ""))
        assert t.status_code == 200, t.text

    def add_manual_data_v2(self, start: datetime.datetime, duration: float, tag: str,
                           afk_data, manual_data, overlap='overwrite',
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
        :param exclude_afk_time: bool if True only add the tag to time that is not afk
        :return:
        """

        assert overlap in ["overwrite", "underwrite", "raise", 'delete']
        stop = start + datetime.timedelta(seconds=duration)
        start = pd.to_datetime(start).round('T')
        stop = pd.to_datetime(stop).round('T')

        manual_start = start
        manual_stop = stop
        if manual_data is not None:
            manual_start = manual_data.start.round('T').min()
            manual_stop = manual_data.stop.round('T').max()

        all_data = pd.DataFrame(
            index=pd.date_range(min(start, manual_start),
                                max(stop, manual_stop),
                                freq='T'),
            columns=['afk', 'prev_manual_id', 'make', 'new_tag', 'prev_tag']
        )
        all_data.loc[:, 'afk'] = True
        all_data.loc[:, 'prev_manual_id'] = None
        all_data.loc[:, 'make'] = False
        all_data.loc[:, 'new_tag'] = None
        all_data.loc[:, 'prev_tag'] = None

        all_data.loc[start:stop, 'make'] = True
        all_data.loc[start:stop, 'new_tag'] = tag

        if exclude_afk_time:
            if afk_data is not None:
                not_afk_data = afk_data.loc[afk_data.status != 'afk']
                for astart, astop in not_afk_data.loc[:, ['start', 'stop']].itertuples(False, None):
                    astart = astart.round('T')
                    astop = astop.round('T')
                    all_data.loc[astart:astop, 'afk'] = False
                else:
                    warnings.warn('no afk data found, not excluding afk time')
            all_data.loc[all_data.afk, 'make'] = False

        if manual_data is not None:
            for mid, mstart, mstop, t in manual_data.loc[:, ['start', 'stop', 'tag']].itertuples(True, None):
                mstart = mstart.round('T')
                mstop = mstop.round('T') - pd.Timedelta(minutes=1)
                all_data.loc[mstart:mstop, 'prev_manual_id'] = mid
                all_data.loc[mstart:mstop, 'prev_tag'] = t

        events = []
        delete_events = []
        if overlap == 'delete':
            delete_events.extend(all_data.loc[all_data.new_tag.notna(), 'prev_manual_id'].dropna().unique())
        elif overlap == "overwrite":
            delete_events.extend(all_data.loc[:, 'prev_manual_id'].dropna().unique())
            for mid in delete_events:
                idx = (all_data.loc[:, 'prev_manual_id'] == mid) & (all_data.loc[:, 'new_tag'].isna())
                all_data.loc[idx, 'make'] = True
                idx = (all_data.loc[:, 'prev_manual_id'] == mid) & (all_data.loc[:, 'new_tag'].notna())
                all_data.loc[idx, 'prev_tag'] = None


        elif overlap == "underwrite":
            all_data.loc[all_data.prev_manual_id.notna(), 'make'] = False
        elif overlap == "raise":
            if (all_data.loc[:, 'prev_manual_id'].notna() & all_data.make).any():
                raise ValueError('stopped to prevent overlapping events')
        else:
            raise ValueError("should not get here")

        # make events
        all_data = all_data.loc[all_data.make]
        if overlap != 'delete' and not all_data.empty:
            assert (all_data.loc[:, ['prev_tag', 'new_tag']].notna().sum(axis=1) == 1).all()
            all_data.loc[:, 'make_tag'] = None
            all_data.loc[all_data.prev_tag.notna(), 'make_tag'] = all_data.loc[all_data.prev_tag.notna(), 'prev_tag']
            all_data.loc[all_data.new_tag.notna(), 'make_tag'] = all_data.loc[all_data.new_tag.notna(), 'new_tag']
            for t in all_data.make_tag.unique():
                events.extend(self._create_events_from_regular_data(all_data.loc[all_data.make_tag == t], t))

        for idv in pd.unique(delete_events):
            self.delete_manual_data(idv)

        with ActivityWatchClient(client_name=self.client_name) as aw:
            for event in events:
                aw.insert_event(self.manual_bucket_id, event=event)

    def get_manual(self, fromdatetime: str, todatetime: str) -> pd.DataFrame:
        """
        return manual data in utc time
        :param fromdatetime: local time zone iso format
        :param todatetime: local time zone iso format
        :return:
        """

        query = (f'manual = flood(query_bucket(find_bucket("{self.manual_bucket_id}")));\n' +
                 'RETURN = {"events": manual};')

        # manage timezones and daylight savings time..., looks like aw logs in utc.
        fromdatetime = datetime.datetime.fromisoformat(fromdatetime).astimezone(datetime.timezone.utc)
        todatetime = datetime.datetime.fromisoformat(todatetime).astimezone(datetime.timezone.utc)

        with ActivityWatchClient(client_name=self.client_name) as aw:
            if self.manual_bucket_id not in aw.get_buckets().keys():
                raise NotImplementedError('manual bucket had not been created yet')
            data = aw.query(query, [(fromdatetime, todatetime)])
            t = aw.get_events(self.manual_bucket_id, start=fromdatetime, end=todatetime)
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
        df["start"] = pd.to_datetime(df["timestamp"], format='mixed')
        df["stop"] = df.loc[:, 'start'] + df.loc[:, 'duration']
        df.set_index("id", inplace=True)

        df.loc[:, 'start_unix'] = [e.timestamp() for e in df.loc[:, 'start']]
        df.loc[:, 'stop_unix'] = [e.timestamp() for e in df.loc[:, 'stop']]

        temp = (df.loc[:, 'stop_unix'] - df.loc[:, 'start_unix']) / 60
        df.loc[:, 'duration_min'] = temp

        return df

    def get_afk_data(self, fromdatetime: str, todatetime: str) -> pd.DataFrame:
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

        with ActivityWatchClient(client_name=self.client_name) as aw:
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
        df["start"] = pd.to_datetime(df["timestamp"], format='mixed')
        df["stop"] = df.loc[:, 'start'] + df.loc[:, 'duration']
        df.set_index("id", inplace=True)

        df.loc[:, 'start_unix'] = [e.timestamp() for e in df.loc[:, 'start']]
        df.loc[:, 'stop_unix'] = [e.timestamp() for e in df.loc[:, 'stop']]

        temp = (df.loc[:, 'stop_unix'] - df.loc[:, 'start_unix']) / 60
        df.loc[:, 'duration_min'] = temp
        return df

    @staticmethod
    def get_total_untagged_not_afk_data(afk_data, manual_data):
        """
        return seconds of untagged notafk time
        :param afk_data: akf data
        :param manual_data: manual data
        :return: seconds of time not in a manual tag and not afk
        """
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

    def get_window_watcher_data(self, fromdatetime: str, todatetime: str) -> pd.DataFrame:
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

        with ActivityWatchClient(client_name=self.client_name) as aw:
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
        df["start"] = pd.to_datetime(df["timestamp"], format='mixed')
        df["stop"] = df.loc[:, 'start'] + df.loc[:, 'duration']
        df.set_index("id", inplace=True)

        df.loc[:, 'start_unix'] = [e.timestamp() for e in df.loc[:, 'start']]
        df.loc[:, 'stop_unix'] = [e.timestamp() for e in df.loc[:, 'stop']]

        temp = (df.loc[:, 'stop_unix'] - df.loc[:, 'start_unix']) / 60
        df.loc[:, 'duration_min'] = temp

        return df

    @staticmethod
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

    @staticmethod
    def _create_events_from_regular_data(data, tag):
        use_data = pd.DataFrame(index=np.arange(len(data)))
        use_data.loc[:, 'start'] = pd.Series(data.index)
        use_data.loc[:, 'shifter'] = pd.Series(data.index).shift(1)
        use_data.loc[0, 'shifter'] = use_data.loc[1, 'shifter'] - pd.Timedelta(minutes=1)
        use_data.loc[:, 'group'] = (use_data.start != use_data.shifter + pd.Timedelta(minutes=1)).cumsum()

        total_data = use_data.groupby('group').agg({'start': 'min', 'shifter': 'count'})

        events = []
        for s, d in total_data.itertuples(False, None):
            temp = Event(timestamp=s.to_pydatetime(), duration=d * 60,
                         data=dict(tag=tag))
            events.append(temp)
        return events

    def _test_create_events_from_regular_data(self):
        t = pd.Series(pd.date_range('2021-01-01', '2021-01-02', freq='T', tz=datetime.timezone.utc))
        t = t.drop([15, 21, 45, 500])
        events = self._create_events_from_regular_data(pd.DataFrame(index=t), 'test')

        expected_starts = [
            datetime.datetime(year=2021, month=1, day=1, hour=0, minute=00, tzinfo=datetime.timezone.utc),
            datetime.datetime(year=2021, month=1, day=1, hour=0, minute=16, tzinfo=datetime.timezone.utc),
            datetime.datetime(year=2021, month=1, day=1, hour=0, minute=22, tzinfo=datetime.timezone.utc),
            datetime.datetime(year=2021, month=1, day=1, hour=0, minute=46, tzinfo=datetime.timezone.utc),
            datetime.datetime(year=2021, month=1, day=1, hour=8, minute=21, tzinfo=datetime.timezone.utc),
        ]
        expected_durs = [15, 5, 23, 454, 940]
        correct = []
        for e, d, s in zip(events, expected_durs, expected_starts):
            correct.append((e.timestamp == s) and (e.duration.total_seconds() == d * 60))
        assert all(correct)


if __name__ == '__main__':
    awd = AwDataAccess('test')
    awd._test_create_events_from_regular_data()
    awd.get_manual((datetime.datetime.now() + datetime.timedelta(hours=-1)).isoformat(),
                   datetime.datetime.now().isoformat())
    pass
