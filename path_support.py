"""
created matt_dumont 
on: 7/10/23
"""
from pathlib import Path
notify_icon_path = Path(__file__).parent.joinpath('notification/kea.png')
sound_path = Path(__file__).parent.joinpath('notification/Kea.mp3')

# parameter files (in .gitignore)
tray_app_state_path = Path(__file__).parent.joinpath('.trayapp_state')
aq_notify_param_path = Path(__file__).parent.joinpath('.notify_overwork_params')
gui_state_path = Path(__file__).parent.joinpath('.gui_state')
notified_file = Path(__file__).parent.joinpath('.notified')
pause_path = Path(__file__).parent.joinpath('.notify_pause')