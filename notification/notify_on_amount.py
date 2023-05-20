"""
created matt_dumont 
on: 18/02/22
"""

import datetime
import os.path
import sys
from copy import deepcopy
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import pandas as pd
from plyer import notification
from api_support.get_data import get_afk_data, get_manual
from playsound import playsound

today = datetime.date.today()
now = datetime.datetime.now()


def read_param_file(param_file):
    with open(param_file, 'r') as f:
        lines = f.readlines()
        lines = [l for l in lines if l[0] != '#']
        limit = float(lines[0]) * 60  # expects decimal hours
        limit_txt = float(lines[1]) * 60  # expects decimal hours
        text_num = lines[2].strip()
        if text_num.lower() == 'none':
            text_num = None
        message = lines[3].strip()
        countdown_start = float(lines[4])  # expects minutes before to let you know that you are almost done
        notifications_start = int(lines[5])  # won't send notification before hour
        notifications_stop = int(lines[6])  # won't send notification after hour
        start_hr = int(lines[7])
        inc_tagtime = lines[8].strip()
        if inc_tagtime.lower() == 'true':
            inc_tagtime = True
        else:
            inc_tagtime = False

        exclude_tags = [l.strip() for l in lines[9].strip().split(',') if l != '']
        key = lines[10].strip()

    return (limit, limit_txt, text_num, message, countdown_start, notifications_start,
            notifications_stop, start_hr, inc_tagtime, exclude_tags, key)


def calc_worked_time(start_time, stop_time, inc_tagtime, exclude_tags):
    fraction = 5
    starts = []
    stops = []
    manual = get_manual(start_time.isoformat(), stop_time.isoformat())
    if manual is not None:
        starts.append(manual.start.min())
        stops.append(manual.stop.max())
    afk = get_afk_data(start_time.isoformat(), stop_time.isoformat())
    if afk is not None:
        starts.append(afk.start.min())
        stops.append(afk.stop.max())
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

    idx = (((data.afk == 'not-afk') & ~np.in1d(data.tag, exclude_tags))
           | ((data.tag.notna()) & ~np.in1d(data.tag, exclude_tags)))

    worked_time = data.loc[idx, 'timestep'].count() * fraction / 60  # minutes

    return worked_time


def notify_on_amount(param_file, notified_file):
    os.makedirs(os.path.dirname(notified_file), exist_ok=True)
    (limit, limit_txt, text_num, message, countdown_start,
     notifications_start, notifications_stop,
     start_hr, inc_tagtime, exclude_tags, key) = read_param_file(param_file)

    start_time = datetime.datetime(today.year, today.month, today.day, hour=start_hr)
    stop_time = start_time + datetime.timedelta(days=1)
    worked_time = calc_worked_time(start_time, stop_time, inc_tagtime, exclude_tags)
    print(f'{worked_time=} {limit=} {limit_txt=}')

    # text notification limits
    if worked_time >= limit_txt:
        if os.path.exists(notified_file):
            with open(notified_file, 'r') as f:
                last_sent = datetime.datetime.fromisoformat(f.readline())
            if last_sent > start_time:
                pass
            else:
                send_message(number=text_num, message=message, key=key)
                with open(notified_file, 'w') as f:
                    f.write(now.isoformat())
        else:
            send_message(number=text_num, message=message, key=key)
            with open(notified_file, 'w') as f:
                f.write(now.isoformat())

    # desktop notification limits
    if worked_time >= limit:
        # send desktop notification if computer is still active
        start = now + datetime.timedelta(minutes=-60)
        tempdata = get_afk_data(start.isoformat(), now.isoformat())
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
    notification.notify(
        # title of the notification,
        title=title,
        message=text,
        app_icon=os.path.join(os.path.dirname(__file__), 'kea.png'),
        timeout=20
    )
    playsound(os.path.join(os.path.dirname(__file__), 'Kea.mp3'))


# todo the play vs not play is based on the environment... need to understand... see /home/matt_dumont/aw_qt_notify/notify_overwork.env
if __name__ == '__main__':
    # the two below are for quick debugging without command line access
    # param_file = '/home/matt_dumont/aw_qt_notify/notify_overwork_params.txt'
    # notified_file = '/home/matt_dumont/aw_qt_notify/notify_overwork_run.txt'
    param_file = sys.argv[1]
    notified_file = sys.argv[2]
    print(f'inputs: {param_file=} {notified_file=}')
    print(sys.path)

    notify_on_amount(param_file, notified_file)
