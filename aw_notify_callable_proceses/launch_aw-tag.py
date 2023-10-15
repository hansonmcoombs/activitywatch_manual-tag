"""
created matt_dumont 
on: 7/02/22
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parents[1]))
from gui.timetag_gui import launce_timetag

if __name__ == '__main__':
    launce_timetag()
