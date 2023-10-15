"""
created matt_dumont 
on: 7/10/23
"""
from PyQt6 import QtWidgets, QtCore, QtGui
import sys
from pathlib import Path
import datetime

sys.path.append(str(Path(__file__).parents[1]))
print(sys.path)
from notification.notify_on_amount import desktop_notification, Notifier
from path_support import icon_path, tray_app_state_path, pause_icon_path
from gui.note_frequency_gui import SetFrequency
from gui.custom_pause_gui import CustomPause
from gui.set_notify_overwork_params_gui import NotifyParams
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

    def __init__(self, app, test_mode=True):
        """

        :param test_mode: bool if True include test notification menu item
        """
        self.notifier = Notifier()
        if tray_app_state_path.exists():
            with open(tray_app_state_path, 'r') as f:
                self.notifying = f.readline().strip() == 'True'
                self.note_frequency = int(f.readline().strip())

        else:
            self.notifying = True
            self.note_frequency = 10
        self.app = app
        self.pause_until = None  # reset any pauses on update

        self.test_mode = test_mode
        self._pause_10 = False
        self._pause_30 = False
        self._pause_60 = False
        self._pause_custom = False
        self._pause_notifications = False

        self.tray = QtWidgets.QSystemTrayIcon()
        self.base_icon = QtGui.QIcon(str(icon_path))
        self.pause_icon = QtGui.QIcon(str(pause_icon_path))
        self.tray.setIcon(self.base_icon)
        self.tray.setVisible(True)
        self._make_menu()
        self.tray.setContextMenu(self.menu)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.notification)
        self.timer.setInterval(1000 * 60 * self.note_frequency)  # convert to ms
        self.timer.start()

    def _make_menu(self):
        self.menu_items = {}
        menu_text = {
            'launch_timetag': 'Launch TimeTag',
            'notifying': 'Notifying Overwork',
            'pause_notifications': 'Pause Notifications',
            'set_notify_params': 'Set Notify Params',
            'set_note_freq': 'Set Notification Frequency',
            'test_notification': 'Test Notification',
            'quit': 'Quit',
        }

        menu_actions = {
            'launch_timetag': self._launch_timetag,
            'notifying': self.set_notifying,
            'pause_notifications': None,
            'set_notify_params': self._launch_notify_params,
            'set_note_freq': self.set_note_frequency,
            'test_notification': _test_notification,
            'quit': self.quit,

        }

        self.menu = QtWidgets.QMenu()
        for k in self.menu_keys:
            kwargs = {}
            if k == 'test_notification' and not self.test_mode:
                continue

            if k == 'pause_notifications':
                self._make_pause_menu()
                continue
            if k == 'notifying':
                kwargs = dict(checkable=True, checked=self.is_checked(k))

            t = QtGui.QAction(menu_text[k], **kwargs)
            t.triggered.connect(menu_actions[k])
            self.menu_items[k] = t
            self.menu.addAction(t)

    def _make_pause_menu(self):
        # pause notifications
        self.pause_menu = QtWidgets.QMenu('Pause Notifications')
        self.menu_items['pause_notifications'] = self.pause_menu
        menu_text = {
            'pause_10': 'Pause 10 min',
            'pause_30': 'Pause 30 min',
            'pause_60': 'Pause 60 min',
            'pause_custom': 'Pause For...',
            'cancel_pause': 'Cancel Pause',
        }

        menu_actions = {
            'pause_10': self.set_pause_10,
            'pause_30': self.set_pause_30,
            'pause_60': self.set_pause_60,
            'pause_custom': self.set_custom_pause,
            'cancel_pause': self.cancel_pause,
        }

        for k in menu_text.keys():
            if k == 'cancel_pause':
                t = QtGui.QAction(menu_text[k])
            else:
                t = QtGui.QAction(menu_text[k], checkable=True, checked=self.is_checked(k))
            t.triggered.connect(menu_actions[k])
            self.menu_items[k] = t
            self.pause_menu.addAction(t)
        self.menu.addMenu(self.pause_menu)

    def _update_checked(self):
        for k in ['pause_10', 'pause_30', 'pause_60', 'pause_custom', 'notifying']:
            self.menu_items[k].setChecked(self.is_checked(k))

        k = 'pause_notifications'
        if self.is_checked(k):
            self.tray.setIcon(self.pause_icon)
        else:
            self.tray.setIcon(self.base_icon)

    def set_notifying(self):
        self.notifying = not self.notifying
        self._update_checked()

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
        self.sub_window = CustomPause()
        self.sub_window.submitClicked.connect(self._set_pause_discrete)
        self.sub_window.show()
        self._update_checked()

    def is_checked(self, k):
        mappers = {
            'pause_10': self._pause_10,
            'pause_30': self._pause_30,
            'pause_60': self._pause_60,
            'pause_custom': self._pause_custom,
            'notifying': self.notifying,
            'pause_notifications': self._pause_notifications,
        }
        return mappers[k]

    def cancel_pause(self):
        self.pause_until = None

        # unchecked all pause items
        self._pause_notifications = False
        self._pause_custom = False
        self._pause_60 = False
        self._pause_30 = False
        self._pause_10 = False
        self._update_checked()

    def _set_notify_frequency(self, nmins):
        if nmins == 'None':
            pass
        else:
            nmins = int(nmins)
            self.note_frequency = nmins
            self.timer.stop()
            self.timer.setInterval(1000 * 60 * self.note_frequency)  # convert to ms
            self.timer.start()

    def _set_pause_discrete(self, nmins):
        print(nmins)
        if nmins == 'None' or nmins == '':
            self.pause_until = None
        else:
            if isinstance(nmins, str):
                self._pause_custom = True
            nmins = int(nmins)
            self.pause_until = datetime.datetime.now() + datetime.timedelta(minutes=nmins)
            self._pause_notifications = True
        self._update_checked()

    def quit(self):
        with open(tray_app_state_path, 'w') as f:
            f.write(str(self.notifying) + '\n')
            f.write(str(self.note_frequency) + '\n')
        self.timer.stop()
        self.app.quit()



    def _launch_notify_params(self):

        def temp():
            pass

        self.sub_window = NotifyParams(self.app)
        self.sub_window.submitClicked.connect(temp)
        self.sub_window.show()

    def _launch_timetag(self):
        subprocess.run([
            sys.executable,
            str(Path(__file__).parents[1].joinpath('aw_notify_callable_proceses/launch_aw-tag.py'))
        ])

    def set_note_frequency(self):
        self.sub_window = SetFrequency(self.note_frequency)
        self.sub_window.submitClicked.connect(self._set_notify_frequency)
        self.sub_window.show()

    def notification(self):
        """
        run the notification loop
        :param icon: need to pass the icon to the function in pystray, so this must be here
        :return:
        """
        run_notification = self.notifying
        # check for pause
        if self.pause_until is not None:
            if datetime.datetime.now() < self.pause_until:
                run_notification = False
                print('notifications paused until', self.pause_until.isoformat())
            else:
                print('pause time expired')
                self.cancel_pause()  # unchecked all pause items
        # run notification
        if run_notification:
            self.notifier.notify_on_amount()
        print(f'waiting {self.note_frequency} minutes')


def _test_notification():
    desktop_notification('test title', 'test message')


def launch_pannel_app(test_mode):
    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    AWTN = AwqtTagNotify(app, test_mode)
    sys.exit(app.exec())



if __name__ == '__main__':
    launch_pannel_app(True)
