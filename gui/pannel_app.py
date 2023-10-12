"""
created matt_dumont 
on: 7/10/23
"""
import time
import pystray
import sys
from pathlib import Path
import datetime
from PIL import Image

sys.path.append(Path(__file__).parents[1])
print(sys.path)
from notification.notify_on_amount import desktop_notification, Notifier
from path_support import pause_path, notify_icon_path, tray_app_state_path, freq_path
import subprocess


class AwqtTagNotify():
    menu_keys = (
        'launch_timetag',
        'notifying',
        'pause_notifications',
        'set_notify_params',
        'set_note_freq',
        'test_notification',
        'quit',
    )
    menu = None

    def __init__(self, test_mode=True):
        """

        :param test_mode: bool if True include test notification menu item # todo document
        """
        self.notifier = Notifier()
        pause_path.unlink(missing_ok=True)  # reset any pauses on restart
        if tray_app_state_path.exists():
            with open(tray_app_state_path, 'r') as f:
                self.notifying = f.readline().strip() == 'True'
                self.note_frequency = int(f.readline().strip())

        else:
            self.notifying = True
            self.note_frequency = 10
        self.in_startup=True
        self.test_mode = test_mode
        self._pause_10 = False
        self._pause_30 = False
        self._pause_60 = False
        self._pause_custom = False
        self._pause_notifications = False
        self._make_menu()
        self.icon = pystray.Icon(name='AwqtTagNotify', icon=self._make_icon(),
                                 menu=self.menu)

    # todo make this actually run the notifications....
    # todo see: https://www.reddit.com/r/learnpython/comments/a7utd7/pystray_python_system_tray_icon_app/
    def _make_menu(self):
        self.menu_items = {}

        # launch aw_qt_tag
        t = pystray.MenuItem('Launch TimeTag', self._launch_timetag, checked=None)
        self.menu_items['launch_timetag'] = t

        # notifying
        t = pystray.MenuItem('Notifying Overwork', self.set_notifying, checked=self.is_checked)
        self.menu_items['notifying'] = t

        self._make_pause_menu()

        # set notify params
        t = pystray.MenuItem('Set Notify Params', self._launch_notify_params, checked=None)
        self.menu_items['set_notify_params'] = t

        # set note frequency
        t = pystray.MenuItem('Set Note Frequency', self._launch_set_note_frequency, checked=None)
        self.menu_items['set_note_freq'] = t

        # test notification option
        t = pystray.MenuItem('Test Notification', _test_notification, checked=None, visible=self.test_mode)
        self.menu_items['test_notification'] = t

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

        t = pystray.MenuItem('Pause 30 min', self.set_pause_30, checked=self.is_checked)
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

    def quit(self):
        with open(tray_app_state_path, 'w') as f:
            f.write(str(self.notifying) + '\n')
            f.write(str(self.note_frequency) + '\n')
        self.icon.stop()

    def run(self):
        self.icon.run(
            self.notification
        )

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

    def _launch_set_note_frequency(self):
        subprocess.run([
            sys.executable,
            str(Path(__file__).parents[1].joinpath('aw_notify_callable_proceses/launch_set_note_freq.py'))
        ])
        if freq_path.exists():
            with open(freq_path, 'r') as f:
                self.note_frequency = int(f.readline().strip())
            freq_path.unlink()

    def notification(self, icon):
        """
        run the notification loop
        :param icon: need to pass the icon to the function in pystray, so this must be here
        :return:
        """
        icon.visible = True
        while True:  # todo this is blocking quit.
            if self.in_startup:
                print('in startup')
                self.in_startup=False
            else:
                run_notification = True
                # check for pause
                if pause_path.exists():
                    with open(pause_path, 'r') as f:
                        pause_time = datetime.datetime.fromisoformat(f.readline())
                    if datetime.datetime.now() < pause_time:
                        run_notification = False
                    else:
                        pause_path.unlink()
                        # unchecked all pause items
                        self._pause_notifications = False
                        self._pause_custom = False
                        self._pause_60 = False
                        self._pause_30 = False
                        self._pause_10 = False

                # run notification
                if run_notification:
                    self.notifier.notify_on_amount()
                print(f'waiting {self.note_frequency} minutes')
                time.sleep(self.note_frequency * 60)


def _test_notification():
    desktop_notification('test title', 'test message')


if __name__ == '__main__':
    t = AwqtTagNotify(True)
    t.run()
