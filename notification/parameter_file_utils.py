"""
created matt_dumont 
on: 7/10/23
"""
parameter_keys = (
    'limit', 'limit_txt', 'text_num', 'message', 'countdown_start', 'notifications_start',
    'notifications_stop', 'start_hr', 'key'

)

questions = dict(
    limit="How many hours do you want to work",
    limit_txt="After how many hours do you want to text the external number",
    text_num="What is the external number you want to text",
    message="What is the message you want to send",
    countdown_start="How many minutes before the limit do you want to be notified",
    notifications_start="What hour do you want to start receiving notifications",
    notifications_stop="What hour do you want to stop receiving notifications",
    start_hr="From what hour do you want to start counting hours (set high, e.g. 4am)",
    key="Textbelt key (default=textbelt, one free text per day)"
)

default_values = dict(
    limit=8,
    limit_txt=8,
    countdown_start=30,
    notifications_start=8,
    notifications_stop=18,
    start_hr=4,
    key='textbelt',
    text_num='',
    message='',

)


def read_param_file(path):
    params = {}
    if path.exists():
        with open(path, 'r') as f:
            lines = f.readlines()

        for l in lines:
            k, v = l.split('=')
            temp = v.strip()
            if k in ['limit', 'limit_txt', 'notifications_start', 'notifications_stop', 'start_hr', 'countdown_start']:
                temp = int(temp)
            params[k.strip()] = temp
    else:
        params = default_values

    assert set(params.keys()) == set(parameter_keys), f'missing parameters: {set(parameter_keys) - set(params.keys())}'
    return params
