"""
created matt_dumont 
on: 6/02/22
"""
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg

app = pg.mkQApp("Plotting Example")
#mw = QtGui.QMainWindow()
#mw.resize(800,800)

win = pg.GraphicsLayoutWidget(show=True, title="Basic plotting exampless")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph example: Plotting')

x2 = np.linspace(-100, 100, 1000)
data2 = np.sin(x2) / x2
p8 = win.addPlot(title="Region Selection")
p8.plot(data2, pen=(255,255,255,200))
lr = pg.LinearRegionItem([400,700])
lr.setZValue(-10)
p8.addItem(lr)

p9 = win.addPlot(title="Zoom on selected region")
p9.plot(data2)
def updatePlot():
    p9.setXRange(*lr.getRegion(), padding=0)
def updateRegion():
    lr.setRegion(p9.getViewBox().viewRange()[0])
lr.sigRegionChanged.connect(updatePlot)
p9.sigXRangeChanged.connect(updateRegion)
updatePlot()

# todo see cross hair/mouse interaction for the printing over
# todo look at linked views for the three rows
# todo add row for each row and one for sums
# todo table widget for output
# todo bar graph is the best option for the plotting...

if __name__ == '__main__':
    pg.exec()
