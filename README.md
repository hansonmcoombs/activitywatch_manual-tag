# ActivityWatch_Manual-Tag

This is a very quick and dirty UI build in pyqtgraph and pyQT6 to interact with ActivityWatch data and to implement
ManicTime style manual time tagging on Linux

Key features:

* show daily usage (timeline)
* create manual tags for time
* sum by app, afk/not-afk, and tag for the selected day

NOTE: this was written with the minimum viable product standards and for personal use, so I would not be surprised if
there are substantial bugs.

## manual tagging

manual tags are written to the ActivityWatch datasets via the aw-client python library. The tags are written to a new
bucket, which is also created. The bucket is named f'ui-manual_{socket.gethostname()}'. Tags are events, with one data
attribute 'tag':str

## manual tag overlap

There are three possible ways to handle manual tag overlaps. They are:

* **"overwrite"**: if the new event overlaps with previous events then all events will deleted and replace with new
  events where the passed (new) event is kept completely and the overlapped events (old) are truncated to prevent any
  overlap in the database
* **"underwrite"**: if the new event overlaps with previous events it will be truncated to prevent any overlapping data.
  The tag may be split into multiple events. Existing events will not be impacted.
* **"raise"**: raises an exception to prevent saving overlapping data.

## installation

* ensure ActivityWatch is installed and active
    * download the latest release: https://activitywatch.net/
    * mkdir ~/activitywatch
    * unzip: unzip {file.zip} -d ~/activitywatch
    * add ~/activitywatch/aw-qt to autostart
    * for more info see: https://docs.activitywatch.net/en/latest/getting-started.html#installation
* clone this repo no need to add root to pythonpath
  * git clone git@github.com:hansonmcoombs/activitywatch_manual-tag.git ~/activitywatch_manual-tag
* install the requisite python environment, see
  * conda env create --file ~/activitywatch_manual-tag/env.yml
  * env.txt --> for a loose list of packages
  * env.yml --> for a specified conda environment
* run .../launch_aw-tag.py to launch using the aforementioned environment
* add menu item
  * settings -> menu editor --> add
    * title: ActivityWatch Tag-Time
  * {path to home}/miniconda3/bin/conda run -n aw_qt python {path to home}/activitywatch_manual-tag/launch_aw-tag.py
  * if you want to be fancy add the aw logo: ~/activitywatch/aw-server/aw_server/static/static/logo.png


# Notification of overwork
A relatively new feature (expect bugs) allows notification as you get close to your work
limits. To use this feature you must set up a regular process to run to notify overwork.
Note at present it will not run while using the manual tag feature (bug).

This will create a desktop notification (with sound) and can optionally text a phone
the texting uses https://textbelt.com and assumes that you only will send 1 message
from your IP address, which is free.  It will only send 1 text per day once you reach your limit.

you can specify whether tagged time is included in you total worked time, and you can 
exclude a set of tags (such as *"personal"*) from your worked time.


## parameter and notified file
* both must be passed to the python script: ./notification/notify_on_amount.py

* you must set up a parameter file see ./notification/example_param_file.txt for an example.
  * this is where you set the different options:
    * The number of hours to work before notification
    * The phone number (or *"none"* to not send texts)
    * The number of minutes before your work limit to start notifying you
    * The start time (local time) for notifications... it should only notify when not-afk, but it doesn't always work
    * The stop time (local time) for notifications... it should only notify when not-afk, but it doesn't always work
    * The start of your day (local time)
    * The whether to count tags as worked time
    * which tags to exclude from the count of work time
* you must also pass a notified file path, but it does not need to exist.  This is where
the functions count the number of texts sent.

## installation and setup ubuntu(xubuntu 20.04 has been tested)

* as per above
* get the correct environment to pass as an environment file to the .service file
  * TODO if the environment is not correct sound and notification will not work...
  * still digging into what the correct environment is
  * I have had success using a non-sudo terminal environment.
* modify the ./notification/notify_overwork.service and ./notification/notify_overwork.timer
* set up these timers using systemd

# Final words
1. Thank you to the ActivityWatch team for implementing for their hard work
2. Sorry for the rough as guts nature of this gui... It was the best I could do with my skill set and availability.
3. If anyone wants to improve this, by all means feel free.