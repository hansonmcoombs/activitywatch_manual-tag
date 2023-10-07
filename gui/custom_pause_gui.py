"""
created matt_dumont 
on: 7/10/23
"""
import datetime
import sys
from path_support import pause_path
from PyQt6 import QtGui, QtWidgets


class CustomPause(QtWidgets.QMainWindow):
    saved = False
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.resize(100, 100)

        # frame box
        vert = QtWidgets.QVBoxLayout()

        # set font stats
        self.font = QtGui.QFont()
        self.sheetstyle = f"color: black; "

        label = QtWidgets.QLabel('How many MINUTES to\npause notifications')
        label.setFont(self.font)
        label.setStyleSheet(self.sheetstyle)
        vert.addWidget(label)
        self.answers = t = QtWidgets.QLineEdit('')
        vert.addWidget(t)
        # save/cancel buttons
        save = QtWidgets.QPushButton('Save')
        save.clicked.connect(self.save)
        cancel = QtWidgets.QPushButton('Cancel')
        cancel.clicked.connect(self.close)
        horiz = QtWidgets.QHBoxLayout()
        horiz.addWidget(save)
        horiz.addWidget(cancel)
        vert.addLayout(horiz)
        w = QtWidgets.QWidget()
        w.setLayout(vert)
        self.setCentralWidget(w)

    def save(self):
        txt = self.answers.text()
        problem = False
        try:
            tval = int(txt)
            if tval <= 0:
                raise ValueError()

        except ValueError:
            problem = True
            mbox = QtWidgets.QMessageBox()
            mbox.setText("Pause duration needs to be a positive integer")
            mbox.setFont(self.font)
            mbox.setStyleSheet(self.sheetstyle)
            mbox.exec()
            return

        with open(pause_path, 'w') as f:
            f.write((datetime.datetime.now() + datetime.timedelta(minutes=tval)).isoformat())
        self.saved = True
        self.close()


def launch_custom_pause():
    app = QtWidgets.QApplication(sys.argv)
    win = CustomPause()
    win.show()
    sys.exit(app.exec())
    save=win.saved
    print(f'{save=}')

if __name__ == '__main__':
    launch_custom_pause()
