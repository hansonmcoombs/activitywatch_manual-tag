notification system still under development/testing if you want
to use the notification system you must
* create an environment file and parameter file and specify these paths along with a check sent path
* copy the service and timer into to be used with system d

# The test notification service
sudo cp /home/matt_dumont/activitywatch_manual-tag/notification/test_notification.service /etc/systemd/system/test_notification.service

# install service files
sudo cp /home/matt_dumont/activitywatch_manual-tag/notification/notify_overwork.service /etc/systemd/system/notify_overwork.service
sudo cp /home/matt_dumont/activitywatch_manual-tag/notification/notify_overwork.timer /etc/systemd/system/notify_overwork.timer

# todo setup signal bot



# todo additoinal stuff needed for pystray
sudo apt install libcairo2-dev pkg-config python3-dev


sudo apt install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-4.0
pip install pystray
pip install manimlib
pip install pycairo
pip install PyGObject