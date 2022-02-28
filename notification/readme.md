notification system still under development/testing if you want
to use the notification system you must
* create an environment file and parameter file and specify these paths along with a check sent path
* copy the service and timer into to be used with system d

sudo cp /home/matt_dumont/PycharmProjects/activitywatch_ui/notification/notify_overwork.service /etc/systemd/system/notify_overwork.service
sudo cp /home/matt_dumont/PycharmProjects/activitywatch_ui/notification/notify_overwork.timer /etc/systemd/system/notify_overwork.timer

# todo check if this worked with terra...  