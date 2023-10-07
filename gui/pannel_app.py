"""
created matt_dumont 
on: 7/10/23
"""

import pystray
import sys
from pathlib import Path
import datetime
from PIL import Image

sys.path.append(Path(__file__).parents[1])
print(sys.path)
from path_support import pause_path, notify_icon_path
import subprocess


# todo need to make notification frequency

class AwqtTagNotify():
    menu_keys = (
        'launch_timetag',
        'notifying',
        'pause_notifications',
        'set_notify_params',
        'quit',
    )
    menu = None

    def __init__(self):  # todo read/save state data to txt file
        self.notifying = True
        self._pause_10 = False
        self._pause_30 = False
        self._pause_60 = False
        self._pause_custom = False
        self._pause_notifications = False
        self._make_menu()
        self.icon = pystray.Icon(name='AwqtTagNotify', icon=self._make_icon(),
                                 menu=self.menu)

    # todo make this actually run the notifications....
    def _make_menu(self):
        self.menu_items = {}

        # launch aw_qt_tag
        t = pystray.MenuItem('Launch TimeTag', self._launch_timetag(), checked=None)
        self.menu_items['launch_timetag'] = t

        # notifying
        t = pystray.MenuItem('Notifying Overwork', self.set_notifying, checked=self.is_checked)
        self.menu_items['notifying'] = t

        self._make_pause_menu()

        # set notify params
        t = pystray.MenuItem('Set Notify Params', self._launch_notify_params, checked=None)
        self.menu_items['set_notify_params'] = t

        # quit
        t = pystray.MenuItem('Quit', self.quit, checked=None)
        self.menu_items['quit'] = t

        self.menu = pystray.Menu(*[self.menu_items[k] for k in self.menu_keys])

    def _make_pause_menu(self):
        # pause notifications
        pause_items = []
        t = pystray.MenuItem('Pause 10 min', self.set_pause_10, checked=self.is_checked)
        pause_items.append(t)
        self.menu_items['pause_10'] = t

        t = pystray.MenuItem('Pause 30 min', self.set_pause_30,
                             checked=self.is_checked)  # todo make sure these are unchecked when pause is over
        pause_items.append(t)
        self.menu_items['pause_30'] = t

        t = pystray.MenuItem('Pause 60 min', self.set_pause_60, checked=self.is_checked)
        pause_items.append(t)
        self.menu_items['pause_60'] = t

        t = pystray.MenuItem('Pause For...', self.set_custom_pause, checked=self.is_checked)
        pause_items.append(t)
        self.menu_items['pause_custom'] = t

        t = pystray.MenuItem('Cancel Pause', self.cancel_pause, checked=None)
        pause_items.append(t)
        self.menu_items['cancel_pause'] = t

        pause_menu = pystray.Menu(*pause_items)
        t = pystray.MenuItem('Pause Notifications', pause_menu, checked=self.is_checked)
        self.menu_items['pause_notifications'] = t

    def set_notifying(self):
        self.notifying = not self.notifying

    def set_pause_10(self):
        self._pause_10 = True
        self._set_pause_discrete(10)

    def set_pause_30(self):
        self._pause_30 = True
        self._set_pause_discrete(30)

    def set_pause_60(self):
        self._pause_60 = True
        self._set_pause_discrete(60)

    def set_custom_pause(self):
        if pause_path.exists():
            pause_path.unlink()
        self._launch_custom_pause()
        if pause_path.exists():
            self._pause_custom = True
            self._pause_notifications = True
        else:
            self.cancel_pause()

    def is_checked(self, item):
        assert isinstance(item, pystray.MenuItem) or isinstance(item, pystray.Menu)
        txt = item.text
        if txt == 'Pause 10 min':
            return self._pause_10
        elif txt == 'Pause 30 min':
            return self._pause_30
        elif txt == 'Pause 60 min':
            return self._pause_60
        elif txt == 'Pause For...':
            return self._pause_custom
        elif txt == 'Pause Notifications':
            return self._pause_notifications
        elif txt == 'Notifying Overwork':
            return self.notifying
        else:
            raise ValueError(f'{txt=} not recognized')

    def cancel_pause(self):
        pause_path.unlink(missing_ok=True)

        # unchecked all pause items
        self._pause_notifications = False
        self._pause_custom = False
        self._pause_60 = False
        self._pause_30 = False
        self._pause_10 = False

    def _set_pause_discrete(self, nmins):
        with open(pause_path, 'w') as f:
            f.write((datetime.datetime.now() + datetime.timedelta(minutes=nmins)).isoformat())
        self._pause_notifications = True

    def _make_icon(self):
        return Image.open(notify_icon_path)

    def quit(self):  # todo write out state data
        self.icon.stop()

    def run(self):
        self.icon.run()

    def _launch_notify_params(self):
        subprocess.run([
            sys.executable,
            str(Path(__file__).parents[1].joinpath('aw_notify_callable_proceses/launch_set_notify_params.py'))
        ])

    def _launch_timetag(self):
        subprocess.run([
            sys.executable,
            str(Path(__file__).parents[1].joinpath('aw_notify_callable_proceses/launch_aw-tag.py'))
        ])

    def _launch_custom_pause(self):
        subprocess.run([
            sys.executable,
            str(Path(__file__).parents[1].joinpath('aw_notify_callable_proceses/launch_custom_pause.py'))
        ])


if __name__ == '__main__':
    t = AwqtTagNotify()
    t.run()
