"""
created matt_dumont 
on: 13/10/23
"""
import sys
from pathlib import Path

sys.path.append(Path(__file__).parents[1])
from gui.pannel_app import launch_pannel_app

if __name__ == '__main__':
    test_mode = False
    if len(sys.argv) > 1:
        if sys.argv[1].lower().capitalize() == 'True':
            test_mode = True

    launch_pannel_app(test_mode)
