"""
created matt_dumont 
on: 6/02/22
"""
import datetime

import pandas as pd
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import numpy as np
from matplotlib.cm import get_cmap
from api_support.get_data import get_afk_data, get_window_watcher_data, get_manual, get_labels_from_unix
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock


# todo some weird time problems!




def add_windowwatcher(pg_plot, start_d):  # todo make these updating see basicplotting updating
    start = datetime.datetime.fromisoformat(start_d)
    data = get_window_watcher_data(start.isoformat(), (start + datetime.timedelta(days=1)).isoformat())
    if data is not None:
        apps = pd.unique(data.loc[:, 'app'])
        cm = get_cmap('gist_ncar')
        n_scens = len(apps)
        colors = [cm(e / n_scens) for e in range(n_scens)]
        for k, c in zip(apps, colors):
            idx = data.loc[:, 'app'] == k
            bg = pg.BarGraphItem(x0=data.loc[idx, 'start_unix'], x1=data.loc[idx, 'stop_unix'], y0=0, y1=1, brush='b')
            pg_plot.addItem(bg)
        data = data.loc[:, ['title', 'app', 'duration_min', 'start_unix', 'stop_unix']]
    return data


def add_afk(pg_plot, start_d):  # todo make these updating see basicplotting updating
    start = datetime.datetime.fromisoformat(start_d)
    data = get_afk_data(start.isoformat(), (start + datetime.timedelta(days=1)).isoformat())
    if data is not None:
        idx = data.status == 'afk'
        bg2 = pg.BarGraphItem(x0=data.loc[idx, 'start_unix'], x1=data.loc[idx, 'stop_unix'], y0=1, y1=2, brush='r')
        idx = data.status != 'afk'
        bg1 = pg.BarGraphItem(x0=data.loc[idx, 'start_unix'], x1=data.loc[idx, 'stop_unix'], y0=1, y1=2, brush='g')

        pg_plot.addItem(bg1)
        pg_plot.addItem(bg2)

        data = data.loc[:, ['status', 'duration_min', 'start_unix', 'stop_unix']]
    return data


def add_manual_data(pg_plot, start_d):  # todo make these updating see basicplotting updating
    start = datetime.datetime.fromisoformat(start_d)
    data = get_manual(start.isoformat(), (start + datetime.timedelta(days=1)).isoformat())
    if data is not None:
        apps = pd.unique(data.loc[:, 'tag'])
        cm = get_cmap('gist_ncar')
        n_scens = len(apps)
        colors = [cm(e / n_scens) for e in range(n_scens)]
        for k, c in zip(apps, colors):
            idx = data.loc[:, 'tag'] == k
            bg = pg.BarGraphItem(x0=data.loc[idx, 'start_unix'], x1=data.loc[idx, 'stop_unix'], y0=2, y1=3, brush='b')
            pg_plot.addItem(bg)
            data = data.loc[:, ['tag', 'duration_min', 'start_unix', 'stop_unix']]
    return data


app = pg.mkQApp("Activity Watcher")
mw = QtGui.QMainWindow()
mw.resize(1500, 900)
win = pg.GraphicsLayoutWidget(show=False, title="test_gui")
area = DockArea()
mw.setCentralWidget(area)
d1 = Dock("main plot", size=(1000, 900), hideTitle=True)
d2 = Dock("tag data", size=(500, 300), hideTitle=True)
d3 = Dock('table_data', size=(500, 600), hideTitle=True)

area.addDock(d1, 'left')
area.addDock(d2, 'right', d1)
area.addDock(d3, 'bottom', d2)

win = pg.GraphicsLayoutWidget(show=False, title="test_gui")
label1 = pg.LabelItem(justify='right')
win.addItem(label1)
win.nextRow()
label2 = pg.LabelItem(justify='right')
win.addItem(label2)
win.nextRow()
label3 = pg.LabelItem(justify='right')
win.addItem(label3)
win.nextRow()
pg_plot = win.addPlot(axisItems={'bottom': pg.DateAxisItem()})
pg_plot.setYRange(0, 3)
pg_plot.setMouseEnabled(x=True, y=False)
pg_plot.resize(1000, 600)
pg_plot.setWindowTitle('pyqtgraph example: Plotting')
start_day = '2022-02-06'
start_dt = datetime.datetime.fromisoformat(start_day)
afk_data = add_afk(pg_plot, start_day)
ww_data = add_windowwatcher(pg_plot, start_day)
manual = add_manual_data(pg_plot, start_day)

lr = pg.LinearRegionItem([start_dt.timestamp() + 3600 * 9,
                          start_dt.timestamp() + 3600 * 10])  # set window to 9 and 10am
lr.setZValue(-10)
pg_plot.addItem(lr)
# hover over info
vb = pg_plot.vb


def mouseMoved(evt):
    pos = evt[0]  ## using signal proxy turns original arguments into a tuple
    if pg_plot.sceneBoundingRect().contains(pos):
        mousePoint = vb.mapSceneToView(pos)
        index = mousePoint.x()
        tag, tag_dur, afk, afk_dur, cur_app, window, ww_dur = get_labels_from_unix(index, afk_data, ww_data, manual)
        text = (f"<span style='font-size: 12pt'>"
                f"{datetime.datetime.fromtimestamp(index).isoformat(sep=' ', timespec='seconds')};"
                f"  Tag: {tag}; {tag_dur}m")
        label1.setText(text)
        text2 = f"<span style='font-size: 12pt'>AKF:{afk}; {afk_dur}m  app:{cur_app}; {ww_dur}"
        label2.setText(text2)
        text3 = f"<span style='font-size: 12pt' Window: {window}"
        label3.setText(text3)
        # label.setText(f"<span style='font-size: 12pt'>x={mousePoint.x():0.1f}")
        # label.setText("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y1=%0.1f</span>,   <span style='color: green'>y2=%0.1f</span>" % (mousePoint.x(), data1[index], data2[index]))


proxy = pg.SignalProxy(pg_plot.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)

d1.addWidget(win)
# todo use dock widgets to do what I want here
# todo datatable to sum up everything
# todo button to add tag

button = QtGui.QPushButton()

### table section
w = pg.TableWidget()
w.resize(500, 500)
w.setWindowTitle('pyqtgraph example: TableWidget')
if ww_data is not None:
    w.setData(ww_data.groupby('app').sum().to_records())

d3.addWidget(w)

mw.show()
if __name__ == '__main__':
    pg.exec()
    pass
