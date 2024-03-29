"""
created matt_dumont 
on: 7/10/23
"""
from PyQt6 import QtGui, QtWidgets, QtCore
from path_support import aq_notify_param_path
from notification.parameter_file_utils import parameter_keys, questions, read_param_file


class NotifyParams(QtWidgets.QWidget):
    submitClicked = QtCore.pyqtSignal(str)

    def __init__(self, app):
        super().__init__()
        self.setWindowTitle('Set Notification Parameters')
        # frame box
        vert = QtWidgets.QVBoxLayout()

        # set font stats
        self.font = QtGui.QFont()
        self.sheetstyle = f"color: black; "
        self.answers = {}
        existing_params = read_param_file(aq_notify_param_path)  # also provides default values

        for l in parameter_keys:
            label = QtWidgets.QLabel(questions[l])
            label.setFont(self.font)
            label.setStyleSheet(self.sheetstyle)
            value = str(existing_params.get(l, ''))
            self.answers[l] = t = QtWidgets.QLineEdit(value)
            vert.addWidget(label)
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
        self.move(app.primaryScreen().geometry().center()- self.rect().center())
        self.setLayout(vert)
        self.show()

    def save(self):
        outlines = []
        problems = []
        for l in parameter_keys:
            if l in ['limit', 'limit_txt', 'notifications_start', 'notifications_stop', 'start_hr', 'countdown_start']:
                txt = self.answers[l].text()
                if txt == '':
                    outlines.append(f'{l}={self.answers[l].text()}\n')
                else:
                    try:
                        tval = int(txt)
                        outlines.append(f'{l}={self.answers[l].text()}\n')
                        if l != 'countdown_start':
                            assert tval > 0
                            assert tval < 24
                    except ValueError:
                        problems.append(f'{l}={txt}, input must be an integer')
                    except AssertionError:
                        problems.append(f'{l}={txt}, input must be between 0 and 24')
            else:
                outlines.append(f'{l}={self.answers[l].text()}\n')

        if len(problems):
            mbox = QtWidgets.QMessageBox()
            mbox.setText("Problems with inputs:\n *  " + '\n *  '.join(problems))
            mbox.setFont(self.font)
            mbox.setStyleSheet(self.sheetstyle)
            mbox.exec()
        else:
            with open(aq_notify_param_path, 'w') as f:
                f.writelines(outlines)
                self.submitClicked.emit(txt)
                self.close()

    def cancel(self):
        self.submitClicked.emit('None')
        self.close()
