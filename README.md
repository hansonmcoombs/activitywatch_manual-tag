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
    * see: https://docs.activitywatch.net/en/latest/getting-started.html#installation
* install the requisite python environment, see
  * env.txt --> for a loose list of packages
  * env.yml --> for a specified conda environment
* clone this repo no need to add root to pythonpath
* run .../launch_aw-tag.py to launch using the aforementioned environment


## Final words
1. Thank you to the ActivityWatch team for implementing for their hard work
2. Sorry for the rough as guts nature of this gui... It was the best I could do with my skill set and availability.
3. If anyone wants to improve this, by all means feel free.