"""
created matt_dumont 
on: 18/02/22
"""

import datetime
from notification.parameter_file_utils import read_param_file
from path_support import aq_notify_param_path, notified_file, sound_path, notify_icon_path
import pandas as pd
from plyer import notification
from api_support.get_data import AwDataAccess
import os
import shutil


class Notifier:

    def __init__(self):
        self.AWD = AwDataAccess('Notifier')

    def calc_worked_time(self, start_time, stop_time):
        fraction = 5
        starts = []
        stops = []
        manual = self.AWD.get_manual(start_time.isoformat(), stop_time.isoformat())
        if manual is not None:
            starts.append(manual.start.min())
            stops.append(manual.stop.max())
        afk = self.AWD.get_afk_data(start_time.isoformat(), stop_time.isoformat())
        if afk is not None:
            starts.append(afk.start.min())
            stops.append(afk.stop.max())
        if len(starts) == 0:
            return 0
        start_series = min(starts)
        stop_series = max(stops)
        data = pd.DataFrame(data=pd.date_range(start_series, stop_series, freq=f'{fraction}S'), columns=['timestep'])
        data.loc[:, 'tag'] = None
        if manual is not None:
            for tag, start, stop in manual.loc[:, ['tag', 'start', 'stop']].itertuples(False, None):
                data.loc[(data.timestep >= start) & (data.timestep <= stop), 'tag'] = tag
        if afk is not None:
            for tag, start, stop in afk.loc[:, ['status', 'start', 'stop']].itertuples(False, None):
                data.loc[(data.timestep >= start) & (data.timestep <= stop), 'afk'] = tag

        idx = (((data.afk == 'not-afk') & ~data['tag'].astype(str).str.contains('#'))
               | ((data.tag.notna()) & ~data['tag'].astype(str).str.contains('#')))

        worked_time = data.loc[idx, 'timestep'].count() * fraction / 60  # minutes

        return worked_time

    def notify_on_amount(self):
        today = datetime.date.today()
        now = datetime.datetime.now()

        params = read_param_file(aq_notify_param_path)
        limit = params['limit'] * 60  # hours to minutes
        limit_txt = params['limit_txt'] * 60  # hours to minutes
        text_num = params['text_num']
        message = params['message']
        countdown_start = params['countdown_start']
        notifications_start = params['notifications_start']
        notifications_stop = params['notifications_stop']
        start_hr = params['start_hr']
        key = params['key']

        start_time = datetime.datetime(today.year, today.month, today.day, hour=start_hr)
        stop_time = start_time + datetime.timedelta(days=1)
        worked_time = self.calc_worked_time(start_time, stop_time)
        print(f'{worked_time=} {limit=} {limit_txt=}')

        # text notification limits
        if text_num != '' and message != '':
            print('trying to send text')
            if worked_time >= limit_txt:
                if notified_file.exists():
                    with open(notified_file, 'r') as f:
                        last_sent = datetime.datetime.fromisoformat(f.readline())
                    if last_sent > start_time:
                        pass
                    else:
                        self.send_message(number=text_num, message=message, key=key)
                        with open(notified_file, 'w') as f:
                            f.write(now.isoformat())
                else:
                    self.send_message(number=text_num, message=message, key=key)
                    with open(notified_file, 'w') as f:
                        f.write(now.isoformat())

        # desktop notification limits
        if worked_time >= limit:
            # send desktop notification if computer is still active
            start = now + datetime.timedelta(minutes=-60)
            tempdata = self.AWD.get_afk_data(start.isoformat(), now.isoformat())
            if tempdata is None:
                print('No data guessing by time of day')
                if now.hour > notifications_start and now.hour < notifications_stop:
                    desktop_notification(f'OVERWORKED {round(worked_time - limit)} min!!',
                                         f'You have overworked {round(worked_time - limit)} minutes, STOP NOW')
            else:
                print('basing notification on activity')
                last_active = tempdata.loc[tempdata.status == 'not-afk', 'duration_min'].sum()
                last_inactive = tempdata.loc[tempdata.status == 'afk', 'duration_min'].sum()
                print(f'{last_active=}, {last_inactive=}')
                if last_active >= 0.15 * (last_inactive + last_active):
                    # 15% of the last hour active... create notificcation
                    desktop_notification(f'OVERWORKED {round(worked_time - limit)} min!!',
                                         f'You have overworked {round(worked_time - limit)} minutes, STOP NOW')

        elif limit - worked_time <= countdown_start:
            desktop_notification('ALMOST DONE WITH WORK',
                                 f'you have {round(limit - worked_time)} minutes to the end of your day')

    @staticmethod
    def send_message(number, message, key):
        if number is None:
            print('no number not sending message')
            return
        import requests
        resp = requests.post('https://textbelt.com/text', {
            'phone': number,
            'message': message,
            'key': key,
        })

        print(resp.json())


def desktop_notification(title, text):
    print('notification')
    # desktop notification + sound
    adder = ''
    if shutil.which('mpg123') is None:
        adder = '\ncould not find mpg123, no sound\ninstall with sudo apt-get install mpg123'
    notification.notify(
        # title of the notification,
        title=title,
        message=text + adder,
        app_icon=str(notify_icon_path),
        timeout=20
    )
    os.system(f"mpg123 {sound_path}")


if __name__ == '__main__':
    nf = Notifier()
    nf.notify_on_amount()
    desktop_notification('test', 'test')
