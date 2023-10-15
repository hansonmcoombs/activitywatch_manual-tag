"""
created matt_dumont 
on: 7/10/23
"""
import datetime
import sys
from PyQt6 import QtGui, QtWidgets, QtCore


class SetFrequency(QtWidgets.QWidget):
    submitClicked = QtCore.pyqtSignal(str)

    def __init__(self, current_note):
        super().__init__()
        self.resize(100, 100)
        self.current_note = current_note
        # frame box
        vert = QtWidgets.QVBoxLayout()

        # set font stats
        self.font = QtGui.QFont()
        self.sheetstyle = f"color: black; "

        label = QtWidgets.QLabel('How frequently would you like to be notified (minutes)?'
                                 f'\n currently set to {self.current_note} minutes')
        label.setFont(self.font)
        label.setStyleSheet(self.sheetstyle)
        vert.addWidget(label)
        self.answers = t = QtWidgets.QLineEdit('')
        vert.addWidget(t)
        # save/cancel buttons
        save = QtWidgets.QPushButton('Set')
        save.clicked.connect(self.save)
        cancel = QtWidgets.QPushButton('Cancel')
        cancel.clicked.connect(self.cancel)
        horiz = QtWidgets.QHBoxLayout()
        horiz.addWidget(save)
        horiz.addWidget(cancel)
        vert.addLayout(horiz)
        self.setLayout(vert)
        self.show()

    def save(self):
        txt = self.answers.text()
        try:
            tval = int(txt)
            if tval <= 0:
                raise ValueError()

        except ValueError:
            mbox = QtWidgets.QMessageBox()
            mbox.setText("Notification Frequency needs to be a positive integer")
            mbox.setFont(self.font)
            mbox.setStyleSheet(self.sheetstyle)
            mbox.exec()
            return
        self.submitClicked.emit(txt)
        self.close()

    def cancel(self):
        self.submitClicked.emit('None')
        self.close()


def launch_set_frequency():
    app = QtWidgets.QApplication(sys.argv)
    win = SetFrequency()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    print(launch_set_frequency())
