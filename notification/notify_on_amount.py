"""
created matt_dumont 
on: 18/02/22
"""

import datetime
import os.path
import sys
from plyer import notification
from api_support.get_data import get_afk_data
from playsound import playsound

today = datetime.date.today()
now = datetime.datetime.now()
start_hr = 4


def notify_on_amount(param_file, notified_file):
    os.makedirs(os.path.dirname(notified_file), exist_ok=True)

    start_time = datetime.datetime(today.year, today.month, today.day, hour=start_hr)
    stop_time = datetime.datetime(today.year, today.month, today.day + 1, hour=start_hr)
    data = get_afk_data(start_time.isoformat(), stop_time.isoformat())
    data = data.groupby('status').sum()
    worked_time = data.loc['not-afk', 'duration_min']  # minutes
    with open(param_file, 'r') as f:
        lines = f.readlines()
        limit = float(lines[0]) * 60  # expects decimal hours
        text_num = lines[1]
        message = lines[2]
        countdown_start = float(lines[3])  # expects minutes before to let you know that you are almost done
        notifications_start = int(lines[4])  # won't send notification before hour
        notifications_stop = int(lines[5])  # won't send notification after hour

    if worked_time >= limit:
        if os.path.exists(notified_file):
            with open(notified_file, 'r') as f:
                last_sent = datetime.datetime.fromisoformat(f.readline())
            if last_sent > start_time:
                pass
            else:
                send_message(number=text_num, message=message)
                with open(notified_file, 'w') as f:
                    f.write(now.isoformat())
        else:
            send_message(number=text_num, message=message)
            with open(notified_file, 'w') as f:
                f.write(now.isoformat())

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
            if last_active >= 0.15 * (last_inactive + last_active):
                # 15% of the last hour active... create notificcation
                desktop_notification(f'OVERWORKED {round(worked_time - limit)} min!!',
                                     f'You have overworked {round(worked_time - limit)} minutes, STOP NOW')

    elif limit - worked_time <= countdown_start:
        desktop_notification('ALMOST DONE WITH WORK',
                             f'you have {round(limit - worked_time)} minutes to the end of your day')


def send_message(number, message):
    import requests
    resp = requests.post('https://textbelt.com/text', {
        'phone': number,
        'message': message,
        'key': 'textbelt',
    })

    print(resp.json())


def desktop_notification(title, text):
    print('notification')
    # desktop notification + sound
    notification.notify(
        # title of the notification,
        title=title,
        message=text,
        app_icon=None,
        timeout=20
    )
    playsound(os.path.join(os.path.dirname(__file__), 'Kea.mp3'))


# todo the play vs not play is based on the environment... need to understand... see /home/matt_dumont/aw_qt_notify/notify_overwork.env
if __name__ == '__main__':
    # param_file = '/home/matt_dumont/aw_qt_notify/notify_overwork_params.txt'
    # notified_file = '/home/matt_dumont/aw_qt_notify/notify_overwork_run.txt'
    param_file = sys.argv[1]
    notified_file = sys.argv[2]
    notify_on_amount(param_file, notified_file)
