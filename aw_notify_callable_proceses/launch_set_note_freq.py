"""
created matt_dumont 
on: 12/10/23
"""
from pathlib import Path
import sys
sys.path.append(Path(__file__).parents[1])
from gui.note_frequency_gui import launch_set_frequency
if __name__ == '__main__':
    launch_set_frequency()