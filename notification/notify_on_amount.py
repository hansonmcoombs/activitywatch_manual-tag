"""
created matt_dumont 
on: 18/02/22
"""

import datetime
import os.path
import sys
from api_support.get_data import get_afk_data

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
        limit = float(lines[0]) * 60 # expects decimal hours
        text_num = lines[1]
        message = lines[2]
        countdown_start = float(lines[3]) # expects minutes before

    if worked_time >= limit:
        if os.path.exists(notified_file):
            with open(notified_file, 'r') as f:
                already_sent = int(f.readline()) # todo change to datetime of last sent
            if already_sent == 1:
                pass
            else:
                send_message(number=text_num, message=message)
                with open(notified_file, 'w') as f:
                    f.write('1')
        else:
            send_message(number=text_num, message=message)
            with open(notified_file, 'w') as f:
                f.write('1')

        # todo send desktop notification if computer is still active
    elif limit-worked_time <= countdown_start:
        desktop_notification(f'you have {round(limit-worked_time)} minutes to the end of your day')

def send_message(number, message):
    import requests
    resp = requests.post('https://textbelt.com/text', {
        'phone': number,
        'message': message,
        'key': 'textbelt',
    })

    print(resp.json())

def desktop_notification(text): # todo make this happen
    # desktop notification + sound
    raise NotImplementedError


if __name__ == '__main__':
    param_file = sys.argv[1]
    notified_file = sys.argv[2]
    notify_on_amount(param_file, notified_file)
