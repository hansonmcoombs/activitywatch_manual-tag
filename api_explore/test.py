"""
created matt_dumont 
on: 5/02/22
"""
import requests
import socket

# todo start here: https://github.com/ActivityWatch/aw-client/blob/master/examples/load_dataframe.py

# general plan create a bucket, then create manual events, then plot everything up

api_base = 'http://localhost:5600/api/'
manual_bucket_id = f'ui-manual_{socket.gethostname()}'

def get_buckets():
    # list buckets
    requests.get(api_base + '/0/buckets/')

    # get bucket aw-watcher-afk_wanganui
    r = requests.get(api_base + '/0/buckets/' + 'aw-watcher-afk_wanganui')

    # get events
    r = requests.get(api_base + '/0/buckets/' + 'aw-watcher-afk_wanganui' + '/events')


def list_buckets():
    """
    return tuple of available buckets
    :return:
    """
    t = requests.get(f'{api_base}/0/buckets/')
    assert t.status_code == 200, t.text
    bucket_names = tuple(t.json().keys())
    return bucket_names


def get_events(bucket_name):
    r = requests.get(f'{api_base}/0/buckets/{bucket_name}/events')
    assert r.status_code == 200, r.text
    events = r.json()
    return events


def get_all_events():
    data = {}
    buckets = list_buckets()
    for bucket in buckets:
        data[bucket] = get_events(bucket)

    return data


def create_bucket(bucket_nm):
    buckets = list_buckets()
    if bucket_nm not in buckets:
        r = requests.post(f'{api_base}0/buckets/{bucket_nm}')
        assert r.status_code == 200, r.text


def create_event():
    # todo manage overwrites etc.
    raise NotImplementedError


def create_manual_event():
    raise NotImplementedError


if __name__ == '__main__':
    create_bucket(manual_bucket_id)
