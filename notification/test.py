"""
created matt_dumont 
on: 20/05/23
"""
import os
import sys
from notification.notify_on_amount import desktop_notification

if __name__ == '__main__':
    print('test notification')
    print('PATH:')
    print('\n * :' + '\n *: '.join(os.environ['PATH'].split(':')))
    print('PYTHONPATH')
    print('\n * :' + '\n *: '.join(sys.path))
    desktop_notification('TEST', 'test notification')