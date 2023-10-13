"""
created matt_dumont 
on: 7/10/23
"""
import datetime
import sys
from path_support import freq_path
from PyQt6 import QtGui, QtWidgets

class SetFrequency(QtWidgets.QMainWindow):
    saved = False
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.resize(100, 100)

        # frame box
        vert = QtWidgets.QVBoxLayout()

        # set font stats
        self.font = QtGui.QFont()
        self.sheetstyle = f"color: black; "

        label = QtWidgets.QLabel('How frequently would you like to be notified (minutes)?')
        label.setFont(self.font)
        label.setStyleSheet(self.sheetstyle)
        vert.addWidget(label)
        self.answers = t = QtWidgets.QLineEdit('')
        vert.addWidget(t)
        # save/cancel buttons
        save = QtWidgets.QPushButton('Set')
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
        with open(freq_path, 'w') as f:
            f.write(str(tval))
        self.close()




def launch_set_frequency():
    app = QtWidgets.QApplication(sys.argv)
    win = SetFrequency()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    print(launch_set_frequency())
