"""
created matt_dumont 
on: 7/10/23
"""
import sys
from pathlib import Path
sys.path.append(Path(__file__).parents[1])
from gui.set_notify_overwork_params_gui import launch_notify_params

if __name__ == '__main__':
    launch_notify_params()
