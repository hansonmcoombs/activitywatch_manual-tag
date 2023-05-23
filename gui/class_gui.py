"""
created matt_dumont 
on: 6/02/22
"""
import datetime
import pandas as pd
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import numpy as np
from api_support.get_data import get_afk_data, get_window_watcher_data, get_manual, get_labels_from_unix, \
    get_total_untagged_not_afk_data, add_manual_data_v2
from notification.notify_on_amount import read_param_file
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock


class AwQtManual(QtWidgets.QMainWindow):
    data_mapper = {
        'sum by: afk': 'afk_data',
        'sum by: app': 'ww_data',
        'sum by: tag': 'manual_data',
    }
    sum_col = {
        'sum by: afk': 'status',
        'sum by: app': 'app',
        'sum by: tag': 'tag',
    }

    def __init__(self, start_day: str, exclude_tags=tuple()):
        QtWidgets.QMainWindow.__init__(self)
        self.exclude_afk_time = False
        self.exclude_tags = tuple(exclude_tags)
        self.bar_plots = []  # to keep track of the barplots that need to be removed
        self.resize(1900, 900)
        area = DockArea()
        self.setCentralWidget(area)
        self.dock1 = Dock("main plot", size=(1200, 900), hideTitle=True)
        self.dock2 = Dock("tag data", size=(300, 300), hideTitle=True)
        self.dock5 = Dock("legend", size=(200, 900), hideTitle=True)
        self.dock4 = Dock("legend", size=(200, 900), hideTitle=True)
        self.dock3 = Dock('table_data', size=(300, 600), hideTitle=True)
        self.legend = {'afk_data': {},
                       'ww_data': {},
                       'manual_data': {}}
        self.legend_widgets = []

        area.addDock(self.dock1, 'left')
        area.addDock(self.dock4, 'right', self.dock1)
        area.addDock(self.dock5, 'right', self.dock4)
        area.addDock(self.dock2, 'right', self.dock5)
        area.addDock(self.dock3, 'bottom', self.dock2)
        self.day = start_day
        self.day_dt = datetime.datetime.fromisoformat(start_day)
        self.inialize_plot_window()
        self.dock1.addWidget(self.plot_window)

        # add plot data
        self.data = {}
        self.data['afk_data'] = self.add_afk()
        self.data['ww_data'] = self.add_windowwatcher()
        self.data['manual_data'] = self.add_manual_data()

        self.initialize_datatable()
        self.initialize_button_section()
        self.timer = QtCore.QTimer()
        self.add_legend()
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start(500)

        self.show()

    def inialize_plot_window(self):
        self.plot_window = pg.GraphicsLayoutWidget(show=False)
        self.plot_label1 = pg.LabelItem(justify='left')
        self.plot_label2 = pg.LabelItem(justify='left')
        self.plot_label3 = pg.LabelItem(justify='left')
        self.plot_window.addItem(self.plot_label1)
        self.plot_window.nextRow()
        self.plot_window.addItem(self.plot_label2)
        self.plot_window.nextRow()
        self.plot_window.addItem(self.plot_label3)
        self.plot_window.nextRow()
        self.plot_yaxis = pg.AxisItem(orientation='left')
        self.plot_yaxis.setTicks([[(0.5, 'Win-watch'), (1.5, 'Afk'), (2.5, 'Tag')]])
        self.data_plot = self.plot_window.addPlot(axisItems={'bottom': pg.DateAxisItem(), 'left': self.plot_yaxis})
        self.data_plot.setYRange(0, 3)
        self.data_plot.setMouseEnabled(x=True, y=False)
        self.data_plot.resize(1000, 600)
        self.data_plot.setWindowTitle('pyqtgraph example: Plotting')

        self.selection = pg.LinearRegionItem([self.day_dt.timestamp() + 3600 * 9,
                                              self.day_dt.timestamp() + 3600 * 10])  # set window to 9 and 10am
        self.selection.setZValue(-10)
        self.data_plot.addItem(self.selection)
        # hover over info
        self.vb = self.data_plot.vb

    def initialize_button_section(self):
        # delete button
        self.delete_button = QtWidgets.QPushButton('Delete tags in selected time')
        self.delete_button.clicked.connect(self.delete_events)
        self.dock2.addWidget(self.delete_button, 0, 0)

        self.date_edit = QtWidgets.QDateEdit(calendarPopup=True)
        self.date_edit.setDateTime(self.day_dt)
        self.date_edit.dateChanged.connect(self.change_date)
        self.dock2.addWidget(self.date_edit, 1, 0)

        self.data_selector = QtWidgets.QComboBox()
        self.data_selector.addItem('sum by: afk')  # afk_data
        self.data_selector.addItem('sum by: app')  # ww_data
        self.data_selector.addItem('sum by: tag')  # manual_data
        self.dock2.addWidget(self.data_selector, 2, 0)
        self.update_datatable(1)
        self.data_selector.currentIndexChanged.connect(self.update_datatable)

        # tag text area
        horizontal = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Tag:")
        self.tag = QtWidgets.QLineEdit('')
        horizontal.addWidget(label)
        horizontal.addWidget(self.tag)
        self.dock2.layout.addLayout(horizontal, 3, 0)

        # overlap option
        self.overlap_option = QtWidgets.QComboBox()
        self.overlap_option.addItem('overwrite')  # afk_data
        self.overlap_option.addItem('underwrite')  # ww_data
        self.overlap_option.addItem('raise')  # manual_data
        self.dock2.addWidget(self.overlap_option, 4, 0)
        self.overlap_option.currentIndexChanged.connect(self.overlap_sel_change)
        self.overlap_sel_change(1)

        # exclude afk checkbox
        self.exclude_afk_checkbox = QtWidgets.QCheckBox("Exclude afk from tag?")
        self.exclude_afk_checkbox.setChecked(False)
        self.dock2.addWidget(self.exclude_afk_checkbox, 5, 0)

        # tag button
        self.tag_button = QtWidgets.QPushButton('Tag selected Time')
        self.tag_button.clicked.connect(self.tag_time)
        self.dock2.addWidget(self.tag_button, 6, 0)

    def initialize_datatable(self):
        self.datatable = pg.TableWidget()
        self.datatable.resize(500, 500)
        self.dock3.addWidget(self.datatable)

    def tag_time(self):
        low, high = self.selection.getRegion()
        add_manual_data_v2(start=datetime.datetime.fromtimestamp(low, datetime.timezone.utc),
                           duration=high - low, tag=self.tag.text().replace('Tag:', ''),
                           overlap=self.overlap,
                           exclude_afk_time=self.exclude_afk_checkbox.isChecked(),
                           afk_data=self.data['afk_data'], manual_data=self.data['manual_data'])
        self.update_plot_data()
        self.update_datatable(1)
        self.update_legend()

    def change_date(self):
        self.day_dt = self.date_edit.date().toPyDate()
        self.day = self.day_dt.isoformat()
        self.day_dt = datetime.datetime.fromisoformat(self.day)
        self.update_plot_data()
        self.update_datatable(1)

        # auto update area
        xs = self.get_databounds()
        self.data_plot.setXRange(*xs, padding=0)

        # set the selector
        self.selection.setRegion((self.day_dt.timestamp() + 3600 * 9,
                                  self.day_dt.timestamp() + 3600 * 10))
        self.update_legend()

    def add_legend(self):
        self.legend_widgets = []
        self.legend_font = QtGui.QFont()
        self.legend_font.setBold(True)
        for lgroup in ['afk_data', 'manual_data']:
            litems = self.legend[lgroup]
            over_label = QtWidgets.QLabel(lgroup, self)
            over_label.setFont(self.legend_font)
            self.dock4.addWidget(over_label)
            self.legend_widgets.append(over_label)
            for k, c in litems.items():
                leg_lab = QtWidgets.QLabel(k, self)
                leg_lab.setFont(self.legend_font)
                use_c = c if isinstance(c, str) else c.name()
                # setting up background color and border
                leg_lab.setStyleSheet(f"background-color: {use_c}; border: 1px solid black;")
                self.dock4.addWidget(leg_lab)
                self.legend_widgets.append(leg_lab)

        for lgroup in ['ww_data']:
            litems = self.legend[lgroup]
            over_label = QtWidgets.QLabel(lgroup, self)
            over_label.setFont(self.legend_font)
            self.dock5.addWidget(over_label)
            self.legend_widgets.append(over_label)
            for k, c in litems.items():
                leg_lab = QtWidgets.QLabel(k, self)
                leg_lab.setFont(self.legend_font)
                use_c = c if isinstance(c, str) else c.name()
                # setting up background color and border
                leg_lab.setStyleSheet(f"background-color: {use_c}; border: 1px solid black;")
                self.dock5.addWidget(leg_lab)
                self.legend_widgets.append(leg_lab)

    def delete_legend(self):
        while len(self.legend_widgets) > 0:
            li = self.legend_widgets.pop()
            li.setParent(None)
            self.layout().removeWidget(li)
            li.deleteLater()
            li = None

    def get_databounds(self):
        data = []
        for v in self.data.values():
            if v is None:
                continue
            data.append(v.start_unix.min())
            data.append(v.stop_unix.max())
        if len(data) == 0:
            return self.day_dt.timestamp(), (self.day_dt + datetime.timedelta(days=1)).timestamp()
        else:
            return min(data), max(data)

    def overlap_sel_change(self, i):
        self.overlap = self.overlap_option.currentText()

    def update_legend(self):
        self.delete_legend()
        self.add_legend()

    def delete_events(self):
        self.delete_legend()
        low, high = self.selection.getRegion()
        add_manual_data_v2(start=datetime.datetime.fromtimestamp(low, datetime.timezone.utc),
                           duration=high - low, tag=self.tag.text().replace('Tag:', ''),
                           overlap='delete', afk_data=self.data['afk_data'], manual_data=self.data['manual_data'])
        self.update_plot_data()
        self.update_datatable(1)
        self.update_legend()

    def update_datatable(self, i):
        j = self.data_selector.currentText()
        dataset_name = self.data_mapper[j]
        data = self.data[dataset_name]
        if data is not None:
            df = data[[self.sum_col[j],'duration_min']].groupby(self.sum_col[j]).sum().loc[:, ['duration_min']]
            df.loc['total'] = df.sum()
            if dataset_name == 'manual_data' and len(self.exclude_tags) > 0:
                exclude_time = df.loc[df.index[np.in1d(df.index, self.exclude_tags)]].sum()
                untagged_notafk = get_total_untagged_not_afk_data(self.data['afk_data'], self.data['manual_data']) / 60
                df.loc['exclude tags'] = exclude_time
                df.loc['untag(~afk)'] = untagged_notafk
                df.loc['total - exclude tags'] = df.loc['total'] - exclude_time
                df.loc['total + untag(~afk)'] = df.loc['total'] + untagged_notafk
                df.loc['total + untag(~afk) - exclude tags'] = df.loc['total'] - exclude_time + untagged_notafk

            df.loc[:, 'duration_format'] = [f'{int(e // 60):02d}:{int(e % 60):02d}' for e in df.duration_min]
            temp = df.loc[:, ['duration_format']].to_records()
            self.show_data = temp
        else:
            data = pd.DataFrame(columns=['duration min'])
            data.index.name = self.sum_col[j]
            self.show_data = data.to_records()
        self.datatable.setData(self.show_data)

    def mouseMoved(self, evt):
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.data_plot.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)
            index = mousePoint.x()
            tag, tag_dur, afk, afk_dur, cur_app, window, ww_dur = get_labels_from_unix(
                index,
                self.data['afk_data'],
                self.data['ww_data'],
                self.data['manual_data'])
            low, high = self.selection.getRegion()
            selected = (high - low) / 60
            text = (f"<span style='font-size: 12pt'>"
                    f"selection: {int(selected // 60):02d}:{int(selected % 60):02d};"
                    f"  Tag: {tag}; {int(tag_dur // 60):02d}:{int(tag_dur % 60):02d}")
            self.plot_label1.setText(text)
            text2 = (f"<span style='font-size: 12pt'>AKF:{afk}; {int(afk_dur // 60):02d}:{int(afk_dur % 60):02d}  "
                     f"app:{cur_app}; {int(ww_dur // 60):02d}:{int(ww_dur % 60):02d}")
            self.plot_label2.setText(text2)
            text3 = f"<span style='font-size: 12pt'> Window: {window}"
            self.plot_label3.setText(text3)

    def update_plot_data(self):
        self.data_plot.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
        for bg in self.bar_plots:
            self.data_plot.removeItem(bg)
        self.data['manual_data'] = self.add_manual_data()
        self.data['afk_data'] = self.add_afk()
        self.data['ww_data'] = self.add_windowwatcher()

    def add_windowwatcher(self):
        start = datetime.datetime.fromisoformat(self.day)
        data = get_window_watcher_data(start.isoformat(), (start + datetime.timedelta(days=1)).isoformat())
        legend = {}
        if data is not None:
            apps = pd.unique(data.loc[:, 'app'])
            cm = pg.colormap.get('gist_earth', 'matplotlib')
            n_scens = len(apps) + 1
            colors = [cm[(e + 1) / n_scens] for e in range(n_scens)]
            for k, c in zip(apps, colors):
                legend[k] = c
                idx = data.loc[:, 'app'] == k
                bg = pg.BarGraphItem(x0=data.loc[idx, 'start_unix'], x1=data.loc[idx, 'stop_unix'], y0=0, y1=1,
                                     brush=c)
                self.bar_plots.append(bg)
                self.data_plot.addItem(bg)
            self.legend['ww_data'] = legend
        return data

    def add_afk(self):
        start = datetime.datetime.fromisoformat(self.day)
        data = get_afk_data(start.isoformat(), (start + datetime.timedelta(days=1)).isoformat())
        r = QtGui.QColor(255, 0, 0)
        g = QtGui.QColor(0, 225, 0)
        legend = {'not-afk': g, 'afk': r}
        if data is not None:
            idx = data.status == 'afk'
            bg2 = pg.BarGraphItem(x0=data.loc[idx, 'start_unix'], x1=data.loc[idx, 'stop_unix'], y0=1, y1=2,
                                  brush=r)
            idx = data.status != 'afk'
            bg1 = pg.BarGraphItem(x0=data.loc[idx, 'start_unix'], x1=data.loc[idx, 'stop_unix'], y0=1, y1=2,
                                  brush=g)

            self.data_plot.addItem(bg1)
            self.data_plot.addItem(bg2)
            self.bar_plots.append(bg1)
            self.bar_plots.append(bg2)
            self.legend['afk_data'] = legend
        return data

    def add_manual_data(self):
        start = datetime.datetime.fromisoformat(self.day)
        data = get_manual(start.isoformat(), (start + datetime.timedelta(days=1)).isoformat())
        legend = {}
        if data is not None:
            apps = pd.unique(data.loc[:, 'tag'])
            cm = pg.colormap.get('gist_earth', 'matplotlib')
            n_scens = len(apps) + 1
            colors = [cm[(e + 1) / n_scens] for e in range(n_scens)]
            for k, c in zip(apps, colors):
                legend[k] = c
                idx = data.loc[:, 'tag'] == k
                bg = pg.BarGraphItem(x0=data.loc[idx, 'start_unix'], x1=data.loc[idx, 'stop_unix'], y0=2, y1=3,
                                     brush=c)
                self.data_plot.addItem(bg)
                self.bar_plots.append(bg)
            self.legend['manual_data'] = legend

        return data


def main():
    from pathlib import Path
    try:
        (limit, limit_txt, text_num, message, countdown_start, notifications_start,
         notifications_stop, start_hr, inc_tagtime, exclude_tags, key) = read_param_file(
            Path.home().joinpath('aw_qt_notify/notify_overwork_params.txt'))
    except Exception:
        exclude_tags = []
        pass
    app = pg.mkQApp()
    loader = AwQtManual(datetime.date.today().isoformat(), exclude_tags=exclude_tags)
    proxy = pg.SignalProxy(loader.data_plot.scene().sigMouseMoved, rateLimit=60, slot=loader.mouseMoved)
    pg.exec()
