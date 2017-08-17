# This file is part of Firemix.
#
# Copyright 2013-2016 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Firemix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Firemix.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division

from builtins import next
from builtins import str
from builtins import range
from past.utils import old_div
import time
import os
import numpy as np
import math

from PyQt5.QtCore import pyqtSlot, QTimer, Qt, QRect
from PyQt5.QtGui import QColor, QIcon, QImage, QPixmap
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QAbstractItemView, QListWidgetItem, \
                            QTableWidgetItem, QDialog

from ui.ui_firemix import Ui_FireMixMain
from ui.dlg_add_preset import DlgAddPreset
from ui.dlg_settings import DlgSettings

from lib.colors import hsv_float_to_rgb_uint8

class FireMixGUI(QMainWindow, Ui_FireMixMain):

    def __init__(self, parent=None, app=None):
        super(FireMixGUI, self).__init__(parent)
        self.app = app
        self.mixer = app.mixer
        self.setupUi(self)

        geom_str = self.app.settings.get("window-geometry", None)
        if geom_str is not None:
            self.setGeometry(QRect(*geom_str))

        self.icon_blank = QIcon("./res/icons/blank.png")
        self.icon_disabled = QIcon("./res/icons/ic_do_not_disturb_black_24dp_1x.png")
        self.icon_playing = QIcon("./res/icons/ic_play_circle_filled_black_24dp_1x.png")
        self.icon_next = QIcon("./res/icons/ic_play_circle_outline_black_24dp_1x.png")

        self.transition_right_to_left = False
        self.transition_in_progress = False

        # Control
        self.btn_runfreeze.clicked.connect(self.on_btn_runfreeze)
        self.btn_playpause.clicked.connect(self.on_btn_playpause)
        self.btn_next_preset.clicked.connect(self.on_btn_next_preset)
        self.btn_reset_preset.clicked.connect(self.on_btn_reset_preset)
        self.btn_add_preset.clicked.connect(self.on_btn_add_preset)
        self.btn_remove_preset.clicked.connect(self.on_btn_remove_preset)
        self.btn_clone_preset.clicked.connect(self.on_btn_clone_preset)
        self.btn_clear_playlist.clicked.connect(self.on_btn_clear_playlist)
        self.slider_global_dimmer.valueChanged.connect(self.on_slider_dimmer)
        self.slider_speed.valueChanged.connect(self.on_slider_speed)
        self.slider_transition.valueChanged.connect(self.on_slider_transition)
        self.btn_shuffle_playlist.clicked.connect(self.on_btn_shuffle_playlist)
        self.btn_trigger_onset.clicked.connect(self.on_btn_trigger_onset)

        def slider_double_click_event(e):
            self.on_slider_speed_double_click()

        self.slider_speed.mouseDoubleClickEvent = slider_double_click_event

        # File menu
        self.action_file_load_scene.triggered.connect(self.on_file_load_scene)

        self.action_file_new_playlist.triggered.connect(self.on_file_new_playlist)
        self.action_file_open_playlist.triggered.connect(self.on_file_open_playlist)
        self.action_file_save_playlist_as.triggered.connect(self.on_file_save_playlist_as)
        self.action_file_save_playlist.triggered.connect(self.on_file_save_playlist)
        self.action_file_quit.triggered.connect(self.close)


        # Edit menu
        self.action_file_reload_presets.triggered.connect(self.on_file_reload_presets)
        self.action_edit_settings.triggered.connect(self.on_edit_settings)
        #self.action_settings_networking.triggered.connect(self.on_settings_networking)

        # Tools menu
        self.action_file_generate_default_playlist.triggered.connect(self.on_file_generate_default_playlist)

        # Pattern list
        self.lst_presets.itemDoubleClicked.connect(self.on_preset_double_clicked)
        self.lst_presets.itemChanged.connect(self.on_preset_name_changed)
        self.lst_presets.layout_changed.connect(self.on_playlist_reorder)
        self.lst_presets.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lst_presets.customContextMenuRequested.connect(self.preset_list_context_menu)
        self.lst_presets.setEditTriggers(QAbstractItemView.EditKeyPressed | QAbstractItemView.SelectedClicked)

        # Settings
        self.edit_preset_duration.valueChanged.connect(self.on_preset_duration_changed)
        self.edit_transition_duration.valueChanged.connect(self.on_transition_duration_changed)
        self.cb_transition_mode.currentIndexChanged.connect(self.on_transition_mode_changed)
        self.cb_simulate_audio.stateChanged.connect(self.app.mixer.audio.enable_simulation)

        # Pattern Parameters
        self.tbl_preset_parameters.itemChanged.connect(self.on_preset_parameter_changed)
        self.tbl_preset_parameters_item_changed_connected = True
        self.tbl_preset_parameters.cellDoubleClicked.connect(self.on_double_click_preset_parameter)

        self.just_clicked = False

        self.update_playlist()
        self.load_preset_parameters_table()
        self.tbl_preset_parameters.setDisabled(True)
        self.app.playlist_changed.connect(self.on_playlist_changed)

        self.fft_pixmap = None
        self.fft_max = []

        if self.mixer.aubio_connector is not None:
            self.mixer.audio.onset.connect(self.onset_detected)
            self.mixer.aubio_connector.fft_data.connect(self.draw_fft)

        # Mixer FPS update
        self._update_interval = 250
        self.mixer_update_timer = QTimer()
        self.mixer_update_timer.setInterval(self._update_interval)
        self.mixer_update_timer.timeout.connect(self.update_mixer)
        self.mixer_update_timer.start()

        self.transition_update_toggle = False
        self.transition_update_timer = QTimer()
        self.transition_update_timer.setInterval(300)
        self.transition_update_timer.timeout.connect(self.on_transition_update_timer)
        self.mixer.transition_starting.connect(self.transition_update_start)

        self.update_mixer_settings()

        self.app.qt_app.aboutToQuit.connect(self.about_to_quit)

    @pyqtSlot()
    def about_to_quit(self):
        rect = self.geometry()
        self.app.settings["window-geometry"] = [rect.x(), rect.y(),
                                                rect.width(), rect.height()]
        self.app.settings.save()

    def closeEvent(self, event):
        self.app.stop()
        event.accept()

    @pyqtSlot()
    def onset_detected(self):
        self.btn_receiving_audio.setStyleSheet("* { font: bold; color: black }")
        QTimer.singleShot(100, self.clear_onset_detected)

    @pyqtSlot()
    def clear_onset_detected(self):
        self.btn_receiving_audio.setStyleSheet("* { font: normal }")

    @pyqtSlot(bool)
    def audio_simulate_enabled(self, en):
        self.cb_simulate_audio.setChecked(en)

    def on_btn_trigger_onset(self):
        self.app.mixer.onset_detected()
        self.onset_detected()

    def on_slider_transition(self):
        if not self.mixer.is_paused():
            return

        v = (old_div(self.slider_transition.value(), 100.0))

        if self.transition_right_to_left:
            self.mixer.scrub_transition(1.0 - v)
        else:
            self.mixer.scrub_transition(v)


    def transition_update_start(self):
        if self.transition_right_to_left:
            self.slider_transition.setValue(100)
        else:
            self.slider_transition.setValue(0)
        self.slider_transition.setStyleSheet("QSlider { background-color: rgba(100, 100, 255, 50); }")
        self.transition_in_progress = True
        self.transition_update_timer.start()

    def on_transition_update_timer(self):
        p = self.mixer.transition_progress

        if self.transition_update_toggle and not self.mixer.is_paused:
            self.slider_transition.setStyleSheet("QSlider { background-color: rgba(0, 0, 0, 0); }")
            self.transition_update_toggle = False
        else:
            self.slider_transition.setStyleSheet("QSlider { background-color: rgba(100, 100, 255, 50); }")
            self.transition_update_toggle = True

        if p < 1.0:
            if self.transition_right_to_left:
                p = 1.0 - p
            self.slider_transition.setValue(p * 100)

    def update_mixer(self):
        self.setWindowTitle("FireMix - %s - %0.2f FPS" % (self.app.playlist.name, self.mixer.fps()))

        # Update wibblers
        # TODO (jon) this is kinda inefficient
        if self.app.playlist.get_active_preset() is not None:
            for name, parameter in self.app.playlist.get_active_preset().get_parameters().items():
                pval = parameter.get()
                for i in range(self.tbl_preset_parameters.rowCount()):
                    if self.tbl_preset_parameters.item(i, 0).text() == name:
                        # TODO: For now, all wibblers are float values.  Maybe they should be allowed to be others?
                        if parameter._wibbler is not None:
                            self.tbl_preset_parameters.item(i, 2).setText("= %0.2f" % pval)
                            self.tbl_preset_parameters.item(i, 2).setBackground(QColor(0, 0, 200, 5))
                        else:
                            self.tbl_preset_parameters.item(i, 2).setText("")
                            self.tbl_preset_parameters.item(i, 2).setBackground(QColor(0, 0, 0, 0))

            for name, watch in self.app.playlist.get_active_preset().get_watches().items():
                val = watch.get()
                for i in range(self.tbl_preset_parameters.rowCount()):
                    if self.tbl_preset_parameters.item(i, 0).text() == ("watch(%s)" % name):
                        self.tbl_preset_parameters.item(i, 1).setText(str(val))

        #self.draw_fft()

    @pyqtSlot()
    def draw_fft(self):
        """
        This method is slow.
        But, computers are fast.
        """
        #start = time.clock()
        if self.btn_receiving_audio.text() != "":
            self.btn_receiving_audio.setText("FFT Data Streaming")
        fft_data = self.mixer.audio.fft[0]
        self.fft_max.append(max(fft_data))
        if len(self.fft_max) > 64:
            self.fft_max.pop(0)
        max_val = max(self.fft_max)

        width = 256
        height = 64

        if self.fft_pixmap is None:
            self.fft_pixmap = np.full([height, width * 4], 0, dtype=np.uint8)

        for row in range(height - 1):
            self.fft_pixmap[row] = self.fft_pixmap[row + 1]

        if max_val > 0:
            for x in range(0, width * 4, 4):
                f = np.interp(old_div(x, 4), np.arange(len(fft_data)), fft_data)# / max_val
                #f = math.sqrt(math.sqrt(f))
                self.fft_pixmap[height - 1][x:x + 4] = \
                    (hsv_float_to_rgb_uint8((old_div(x, (4.0 * width)), 1.0, f)) + (255,))


        pm = self.fft_pixmap.flatten()
        img = QImage(pm, width, height, QImage.Format_ARGB32)
        self.fft_graphics_view.setPixmap(QPixmap.fromImage(img))
        #print time.clock() - start

    def on_btn_playpause(self):
        if self.mixer.is_paused():
            self.mixer.cancel_scrub()
            self.mixer.pause(False)
            self.btn_next_preset.setDisabled(False)
            self.slider_transition.setDisabled(True)
        else:
            self.mixer.pause()
            self.btn_next_preset.setDisabled(True)
            self.slider_transition.setDisabled(False)
        self.update_mixer_settings()

    def on_btn_runfreeze(self):
        if self.mixer.is_frozen():
            self.mixer.freeze(False)
            self.btn_runfreeze.setText("Freeze")
        else:
            self.mixer.freeze()
            self.btn_runfreeze.setText("Unfreeze")

    def on_btn_next_preset(self):
        self.mixer.cancel_scrub()
        next(self.mixer)
        self.update_playlist()

    def on_btn_reset_preset(self):
        paused = self.app.mixer.is_paused()
        self.app.mixer.pause()
        self.app.playlist.get_active_preset()._reset()
        self.app.mixer.pause(paused)

    def on_btn_add_preset(self):
        dlg = DlgAddPreset(self)
        dlg.exec_()
        if dlg.result() == QDialog.Accepted:
            if dlg.tabWidget.currentIndex() == 0:
                classname = dlg.cb_preset_type.currentText()
                name = dlg.edit_preset_name.text()
                self.app.playlist.add_preset(classname, name)
            else:
                preset_name = dlg.cb_existing_preset_name.currentText()
                self.app.playlist.add_existing_preset(preset_name)

    def on_btn_remove_preset(self):
        ci = self.lst_presets.currentItem()
        if ci is not None:
            self.app.playlist.remove_preset(ci.text())

    def on_btn_clone_preset(self):
        if self.lst_presets.currentItem() is None:
            return

        old_name = self.lst_presets.currentItem().text()

        self.app.playlist.clone_preset(old_name)
        self.update_playlist()

    def on_btn_clear_playlist(self):
        dlg = QtWidgets.QMessageBox()
        dlg.setWindowTitle("FireMix - Clear Playlist")
        dlg.setText("Are you sure you want to clear the playlist?")
        dlg.setInformativeText("This action cannot be undone.")
        dlg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dlg.setDefaultButton(QtWidgets.QMessageBox.No)
        ret = dlg.exec_()
        if ret == QtWidgets.QMessageBox.Yes:
            self.app.playlist.clear_playlist()
            self.update_playlist()

    def update_mixer_settings(self):
        self.edit_preset_duration.setValue(self.mixer.get_preset_duration())
        self.edit_transition_duration.setValue(self.mixer.get_transition_duration())
        # Populate transition list
        current_transition = self.app.settings.get('mixer')['transition']
        transition_list = [str(t(None)) for t in self.app.plugins.get('Transition')]
        transition_list.insert(0, "Cut")
        transition_list.insert(1, "Random")
        self.cb_transition_mode.clear()
        self.cb_transition_mode.insertItems(0, transition_list)
        self.cb_transition_mode.setCurrentIndex(self.cb_transition_mode.findText(current_transition))

        shuffle_state = Qt.Checked if self.app.settings['mixer']['shuffle'] else Qt.Unchecked
        self.btn_shuffle_playlist.setChecked(shuffle_state)

        preset = self.app.playlist.get_active_preset()
        if preset is not None:
            if not self.mixer.is_paused():
                self.tbl_preset_parameters.setDisabled(True)
                self.lbl_preset_parameters.setTitle("%s Parameters (Pause to Edit)" % preset)
                self.btn_playpause.setText("Pause")
                self.btn_next_preset.setDisabled(False)
                self.slider_transition.setDisabled(True)
            else:
                self.lbl_preset_parameters.setTitle("%s Parameters" % preset)
                self.tbl_preset_parameters.setDisabled(False)
                self.btn_next_preset.setDisabled(True)
                self.slider_transition.setDisabled(False)
                self.btn_playpause.setText("Play")
        else:
            if not self.mixer.is_paused():
                self.btn_playpause.setText("Pause")
            else:
                self.btn_playpause.setText("Play")
            self.btn_next_preset.setDisabled(True)
            self.tbl_preset_parameters.setDisabled(True)
            self.lbl_preset_parameters.setTitle("")

    def on_slider_dimmer(self):
        dval = old_div(self.slider_global_dimmer.value(), 100.0)
        self.app.mixer.global_dimmer = dval
        self.lbl_dimmer.setText("Dimmer [%0.2f]" % dval)

    def on_slider_speed(self):
        sval = round(old_div(self.slider_speed.value(), 1000.0), 2)
        self.app.mixer.global_speed = sval
        self.lbl_speed.setText("Speed [%0.2fx]" % sval)

    def on_slider_speed_double_click(self):
        self.slider_speed.setValue(1000.0)
        self.on_slider_speed()

    def update_playlist(self):
        self.lst_presets.clear()
        presets = self.app.playlist.get()
        current = self.app.playlist.get_active_preset()
        next = self.app.playlist.get_next_preset()
        cur_item = None
        for preset in presets:
            item = QListWidgetItem(preset.name())

            #TODO: Enable renaming in the list when we have a real delegate
            #item.setFlags(item.flags() | Qt.ItemIsEditable)
            if not preset.parameter('allow-playback').get():
                item.setIcon(self.icon_disabled)
            else:
                if preset == current:
                    cur_item = item
                    item.setIcon(self.icon_playing)
                elif preset == next:
                    item.setIcon(self.icon_next)
                else:
                    item.setIcon(self.icon_blank)

            self.lst_presets.addItem(item)

        if cur_item and not self.just_clicked:
            self.lst_presets.scrollToItem(cur_item, QAbstractItemView.PositionAtTop)
        elif self.just_clicked:
            self.just_clicked = False

        if self.transition_in_progress and self.mixer.transition_progress >= 1.0:
            self.slider_transition.setStyleSheet("QSlider { background-color: rgba(0, 0, 0, 0) }")

            if self.transition_right_to_left:
                self.slider_transition.setValue(0)
            else:
                self.slider_transition.setValue(100)

            self.transition_right_to_left = not self.transition_right_to_left
            self.transition_in_progress = False
            self.transition_update_timer.stop()

        if current and next:
            if self.transition_right_to_left:
                self.lbl_transition_left.setText(next.name())
                self.lbl_transition_right.setText(current.name())
            else:
                self.lbl_transition_left.setText(current.name())
                self.lbl_transition_right.setText(next.name())
        else:
            self.lbl_transition_left.setText("")
            self.lbl_transition_right.setText("")

    def on_playlist_changed(self):
        self.update_playlist()
        self.update_mixer_settings()
        self.load_preset_parameters_table()

    def on_playlist_reorder(self):
        names = [self.lst_presets.item(i).text() for i in range(self.lst_presets.count())]
        self.app.playlist.reorder_playlist_by_names(names)

    def on_file_load_scene(self):
        pass

    def on_file_reload_presets(self):
        self.app.mixer.freeze(True)
        self.app.playlist.reload_presets()
        self.app.mixer.freeze(False)

    def preset_list_context_menu(self, point):
        ctx = QtWidgets.QMenu("test")
        action_rename = QtWidgets.QAction("Rename" ,self)
        action_rename.triggered.connect(self.start_rename)
        ctx.addAction(action_rename)
        ctx.exec_(self.lst_presets.mapToGlobal(point))

    def start_rename(self):
        #TODO: Enable renaming in the list when we have a real delegate
        #self.lst_presets.editItem(self.lst_presets.currentItem())
        old_name = self.lst_presets.currentItem().text()
        new_name, ok = QtWidgets.QInputDialog.getText(self, 'Rename Pattern', 'New name', text=old_name)
        if ok and new_name:
            if not self.app.playlist.preset_name_exists(new_name):
                self.app.playlist.rename_preset(old_name, new_name)

    def on_preset_name_changed(self, item):
        pass

    def on_preset_double_clicked(self, preset_item):
        self.just_clicked = True
        self.app.mixer.cancel_transition()
        self.app.playlist.set_active_preset_by_name(preset_item.text())

    def on_preset_duration_changed(self):
        nd = self.edit_preset_duration.value()
        if self.mixer.set_preset_duration(nd):
            self.app.settings['mixer']['preset-duration'] = nd
        self.edit_preset_duration.setValue(self.mixer.get_preset_duration())

    def on_transition_duration_changed(self):
        nd = self.edit_transition_duration.value()
        if self.mixer.set_transition_duration(nd):
            self.app.settings['mixer']['transition-duration'] = nd
        self.edit_transition_duration.setValue(self.mixer.get_transition_duration())

    def on_transition_mode_changed(self):
        if self.app.mixer.set_transition_mode(self.cb_transition_mode.currentText()):
            self.app.settings['mixer']['transition'] = self.cb_transition_mode.currentText()

    def load_preset_parameters_table(self):
        if self.tbl_preset_parameters_item_changed_connected:
            self.tbl_preset_parameters.itemChanged.disconnect(self.on_preset_parameter_changed)
            self.tbl_preset_parameters_item_changed_connected = False
        self.tbl_preset_parameters.clear()

        self.tbl_preset_parameters.setColumnCount(3)
        self.tbl_preset_parameters.horizontalHeader().resizeSection(1, 400)
        self.tbl_preset_parameters.setHorizontalHeaderLabels(('Parameter', 'Value', 'Current'))

        if self.app.playlist.get_active_preset() == None:
            return

        parameters = self.app.playlist.get_active_preset().get_parameters()
        watches = self.app.playlist.get_active_preset().get_watches()
        self.tbl_preset_parameters.setRowCount(len(parameters) + len(watches))
        i = 0
        for name in sorted(parameters, key=lambda x: x):
            parameter = parameters[name]
            key_item = QTableWidgetItem(name)
            key_item.setFlags(Qt.ItemIsEnabled)
            value_item = QTableWidgetItem(parameter.get_as_str())
            current_state_item = QTableWidgetItem("")
            current_state_item.setFlags(Qt.ItemIsEnabled)
            self.tbl_preset_parameters.setItem(i, 0, key_item)
            self.tbl_preset_parameters.setItem(i, 1, value_item)
            self.tbl_preset_parameters.setItem(i, 2, current_state_item)
            i += 1

        for name in sorted(watches, key=lambda x: x):
            watch = watches[name]
            key_item = QTableWidgetItem("watch(%s)" % name)
            key_item.setFlags(Qt.ItemIsEnabled)
            value_item = QTableWidgetItem(watch.get_as_str())
            current_state_item = QTableWidgetItem("")
            current_state_item.setFlags(Qt.ItemIsEnabled)
            self.tbl_preset_parameters.setItem(i, 0, key_item)
            self.tbl_preset_parameters.setItem(i, 1, value_item)
            self.tbl_preset_parameters.setItem(i, 2, current_state_item)
            i += 1

        self.tbl_preset_parameters.itemChanged.connect(self.on_preset_parameter_changed)
        self.tbl_preset_parameters_item_changed_connected = True

    def on_preset_parameter_changed(self, item):
        if item.column() != 1:
            return

        key = self.tbl_preset_parameters.item(item.row(), 0)
        if key.text()[:6] == "watch(":
            return

        par = self.app.playlist.get_active_preset().parameter(key.text())
        try:
            par.set_from_str(item.text())
            item.setText(par.get_as_str())
        except ValueError:
            item.setText(par.get_as_str())

    def on_double_click_preset_parameter(self, row, column):
        txt = self.tbl_preset_parameters.item(row, column).text()

        #TODO: do this in a less silly hard-coded way
        if column == 0 and (txt == "first-preset" or txt == "second-preset"):
            pname = self.tbl_preset_parameters.item(row, 1).text()
            self.app.playlist.set_active_preset_by_name(pname)

    def on_file_new_playlist(self):
        paused = self.app.mixer.is_paused()
        self.app.mixer.stop()
        filename, _ = QFileDialog.getSaveFileName(self, 'Save new playlist file',
                                                  os.path.join(os.getcwd(), "data", "playlists"),
                                                  filter="Playlists (*.json)")
        self.app.playlist.create_new(filename)
        self.app.mixer.start()
        self.app.mixer.pause(paused)

    def on_file_open_playlist(self):
        paused = self.app.mixer.is_paused()
        self.app.mixer.stop()
        old_name = self.app.playlist.filename
        filename, _ = QFileDialog.getOpenFileName(self, 'Open playlist file',
                                                  os.path.join(os.getcwd(), "data", "playlists"),
                                                  filter="Playlists (*.json)")
        name = os.path.split(filename)[1].replace(".json", "")

        self.app.playlist.set_filename(filename)
        if not self.app.playlist.open():
            self.app.playlist.set_filename(old_name)
            QtWidgets.QMessageBox.warning(self, "Error", "Could not open file")
        self.app.mixer.start()
        self.app.mixer.pause(paused)

    def on_file_save_playlist(self):
        self.app.playlist.save()

    def on_file_save_playlist_as(self):
        paused = self.app.mixer.is_paused()
        self.app.mixer.pause()
        filename = self.app.playlist.filename
        filename, _ = QFileDialog.getSaveFileName(self, 'Save playlist file as',
                                                  os.path.join(os.getcwd(), "data", "playlists"),
                                                  filter="Playlists (*.json)")

        if len(filename) > 0:
            self.app.playlist.set_filename(filename)
            self.app.playlist.save()
        self.app.mixer.pause(paused)

    def on_file_generate_default_playlist(self):
        dlg = QtWidgets.QMessageBox()
        dlg.setWindowTitle("FireMix - Generate Default Playlist")
        dlg.setText("Are you sure you want to generate the default playlist?")
        dlg.setInformativeText("All existing playlist entries will be removed.  This action cannot be undone.")
        dlg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dlg.setDefaultButton(QtWidgets.QMessageBox.No)
        ret = dlg.exec_()
        if ret == QtWidgets.QMessageBox.Yes:
            self.app.playlist.generate_default_playlist()
            self.update_playlist()

    def on_edit_settings(self):
        DlgSettings(self).exec_()

    def on_btn_shuffle_playlist(self):
        shuffle = self.btn_shuffle_playlist.isChecked()
        self.app.settings['mixer']['shuffle'] = shuffle
        self.app.playlist.shuffle_mode(shuffle)

