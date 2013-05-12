from PySide import QtGui, QtCore

from ui.ui_firemix import Ui_FireMixMain
from ui.dlg_add_preset import DlgAddPreset
from ui.dlg_setup_networking import DlgSetupNetworking

class FireMixGUI(QtGui.QMainWindow, Ui_FireMixMain):

    def __init__(self, parent=None, app=None):
        super(FireMixGUI, self).__init__(parent)
        self._app = app
        self._mixer = app.mixer
        self.setupUi(self)

        # Control
        self.btn_blackout.clicked.connect(self.on_btn_blackout)
        self.btn_runfreeze.clicked.connect(self.on_btn_runfreeze)
        self.btn_playpause.clicked.connect(self.on_btn_playpause)
        self.btn_next_preset.clicked.connect(self.on_btn_next_preset)
        self.btn_prev_preset.clicked.connect(self.on_btn_prev_preset)
        self.btn_reset_preset.clicked.connect(self.on_btn_reset_preset)
        self.btn_add_preset.clicked.connect(self.on_btn_add_preset)
        self.btn_remove_preset.clicked.connect(self.on_btn_remove_preset)
        self.btn_clone_preset.clicked.connect(self.on_btn_clone_preset)
        self.btn_clear_playlist.clicked.connect(self.on_btn_clear_playlist)

        # File menu
        self.action_file_load_scene.triggered.connect(self.on_file_load_scene)
        self.action_file_reload_presets.triggered.connect(self.on_file_reload_presets)
        self.action_file_save_playlist.triggered.connect(self.on_file_save_playlist)
        self.action_file_quit.triggered.connect(self.close)
        self.action_file_generate_default_playlist.triggered.connect(self.on_file_generate_default_playlist)

        # Settings menu
        self.action_settings_networking.triggered.connect(self.on_settings_networking)

        # Preset list
        self.lst_presets.itemDoubleClicked.connect(self.on_preset_double_clicked)
        self.lst_presets.itemChanged.connect(self.on_preset_name_changed)
        self.lst_presets.layout_changed.connect(self.on_playlist_reorder)
        self.lst_presets.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lst_presets.customContextMenuRequested.connect(self.preset_list_context_menu)
        self.lst_presets.setEditTriggers(QtGui.QAbstractItemView.EditKeyPressed | QtGui.QAbstractItemView.SelectedClicked)

        # Settings
        self.edit_preset_duration.valueChanged.connect(self.on_preset_duration_changed)
        self.edit_transition_duration.valueChanged.connect(self.on_transition_duration_changed)
        self.cb_transition_mode.currentIndexChanged.connect(self.on_transition_mode_changed)

        # Preset Parameters
        self.tbl_preset_parameters.itemChanged.connect(self.on_preset_parameter_changed)

        self.update_playlist()
        self.load_preset_parameters_table()
        self.tbl_preset_parameters.setDisabled(True)
        self._app.playlist_changed.connect(self.on_playlist_changed)

        self.update_mixer_settings()

    def closeEvent(self, event):
        self._app.stop()
        event.accept()

    def on_btn_blackout(self):
        pass

    def on_btn_playpause(self):
        if self._mixer.is_paused():
            self._mixer.pause(False)
            self.tbl_preset_parameters.setDisabled(True)
            self.lbl_preset_parameters.setText("Preset Parameters (Pause to Edit)")
            self.btn_playpause.setText("Pause")
        else:
            self._mixer.pause()
            self.lbl_preset_parameters.setText("Preset Parameters")
            self.tbl_preset_parameters.setDisabled(False)
            self.btn_playpause.setText("Play")

    def on_btn_runfreeze(self):
        if self._mixer.is_frozen():
            self._mixer.freeze(False)
            self.btn_runfreeze.setText("Freeze")
        else:
            self._mixer.freeze()
            self.btn_runfreeze.setText("Unfreeze")

    def on_btn_next_preset(self):
        self._app.playlist.advance()

    def on_btn_prev_preset(self):
        self._app.playlist.advance(-1)

    def on_btn_reset_preset(self):
        self._app.playlist.get_active_preset()._reset()

    def on_btn_add_preset(self):
        dlg = DlgAddPreset(self)
        dlg.exec_()
        if dlg.result() == QtGui.QDialog.Accepted:
            classname = dlg.cb_preset_type.currentText()
            name = dlg.edit_preset_name.text()
            self._app.playlist.add_preset(classname, name)
            self.update_playlist()

    def on_btn_remove_preset(self):
        ci = self.lst_presets.currentItem()
        if ci is not None:
            self._app.playlist.remove_preset(ci.text())
            self.update_playlist()

    def on_btn_clone_preset(self):
        cname = self.lst_presets.currentItem().text()
        current = self._app.playlist.get_preset_by_name(cname)
        classname = current.__class__.__name__
        nname = self._app.playlist.suggest_preset_name(classname)
        self._app.playlist.add_preset(classname, nname)
        self.update_playlist()

    def on_btn_clear_playlist(self):
        dlg = QtGui.QMessageBox()
        dlg.setWindowTitle("FireMix - Clear Playlist")
        dlg.setText("Are you sure you want to clear the playlist?")
        dlg.setInformativeText("This action cannot be undone.")
        dlg.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        dlg.setDefaultButton(QtGui.QMessageBox.No)
        ret = dlg.exec_()
        if ret == QtGui.QMessageBox.Yes:
            self._app.playlist.clear_playlist()
            self.update_playlist()

    def update_mixer_settings(self):
        self.edit_preset_duration.setValue(self._mixer.get_preset_duration())
        self.edit_transition_duration.setValue(self._mixer.get_transition_duration())
        # Populate transition list
        current_transition = self._app.settings.get('mixer')['transition']
        transition_list = [str(t(None)) for t in self._app.plugins.get('Transition')]
        transition_list.insert(0, "Cut")
        self.cb_transition_mode.clear()
        self.cb_transition_mode.insertItems(0, transition_list)
        self.cb_transition_mode.setCurrentIndex(self.cb_transition_mode.findText(current_transition))

    def update_playlist(self):
        self.lst_presets.clear()
        presets = self._app.playlist.get()
        current = self._app.playlist.get_active_preset()
        for preset in presets:
            item = QtGui.QListWidgetItem(preset.get_name())
            #TODO: Enable renaming in the list when we have a real delegate
            #item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

            if preset == current:
                item.setForeground(QtGui.QColor(0, 100, 200))
            self.lst_presets.addItem(item)

    def on_playlist_changed(self):
        self.update_playlist()
        self.load_preset_parameters_table()

    def on_playlist_reorder(self):
        names = [self.lst_presets.item(i).text() for i in range(self.lst_presets.count())]
        self._app.playlist.reorder_playlist_by_names(names)
        self.update_playlist()

    def on_file_load_scene(self):
        pass

    def on_file_reload_presets(self):
        pass

    def preset_list_context_menu(self, point):
        ctx = QtGui.QMenu("test")
        action_rename = QtGui.QAction("Rename" ,self)
        action_rename.triggered.connect(self.start_rename)
        ctx.addAction(action_rename)
        ctx.exec_(self.lst_presets.pos() + self.mapToParent(point))

    def start_rename(self):
        #TODO: Enable renaming in the list when we have a real delegate
        #self.lst_presets.editItem(self.lst_presets.currentItem())
        old_name = self.lst_presets.currentItem().text()
        new_name, ok = QtGui.QInputDialog.getText(self, 'Rename Preset', 'New name', text=old_name)
        if ok and new_name:
            if not self._app.playlist.preset_name_exists(new_name):
                self._app.playlist.rename_preset(old_name, new_name)
                self.update_playlist()

    def on_preset_name_changed(self, item):
        pass

    def on_preset_double_clicked(self, preset_item):
        self._app.playlist.set_active_preset_by_name(preset_item.text())
        self.update_playlist()
        self.load_preset_parameters_table()

    def on_preset_duration_changed(self):
        nd = self.edit_preset_duration.value()
        if self._mixer.set_preset_duration(nd):
            self._app.settings['mixer']['preset-duration'] = nd
        self.edit_preset_duration.setValue(self._mixer.get_preset_duration())

    def on_transition_duration_changed(self):
        nd = self.edit_transition_duration.value()
        if self._mixer.set_transition_duration(nd):
            self._app.settings['mixer']['transition-duration'] = nd
        self.edit_transition_duration.setValue(self._mixer.get_transition_duration())

    def on_transition_mode_changed(self):
        if self._app.mixer.set_transition_mode(self.cb_transition_mode.currentText()):
            self._app.settings['mixer']['transition'] = self.cb_transition_mode.currentText()

    def load_preset_parameters_table(self):
        self.tbl_preset_parameters.clear()
        if self._app.playlist.get_active_preset() == None:
            return

        parameters = self._app.playlist.get_active_preset().get_parameters()
        self.tbl_preset_parameters.setColumnCount(2)
        self.tbl_preset_parameters.setRowCount(len(parameters))
        i = 0
        for name, parameter in parameters.iteritems():
            key_item = QtGui.QTableWidgetItem(name)
            key_item.setFlags(QtCore.Qt.ItemIsEnabled)
            value_item = QtGui.QTableWidgetItem(str(parameter.get()))
            self.tbl_preset_parameters.setItem(i, 0, key_item)
            self.tbl_preset_parameters.setItem(i, 1, value_item)
            i += 1

        self.tbl_preset_parameters.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.tbl_preset_parameters.horizontalHeader().resizeSection(1, 125)

    def on_preset_parameter_changed(self, item):
        if item.column() == 0:
            return
        key = self.tbl_preset_parameters.item(item.row(), 0)
        par = self._app.playlist.get_active_preset().parameter(key.text())
        try:
            par.set_from_str(item.text())
            item.setText(par.get_as_str())
        except ValueError:
            item.setText(par.get_as_str())

    def on_file_save_playlist(self):
        pass

    def on_file_generate_default_playlist(self):
        dlg = QtGui.QMessageBox()
        dlg.setWindowTitle("FireMix - Generate Default Playlist")
        dlg.setText("Are you sure you want to generate the default playlist?")
        dlg.setInformativeText("All existing playlist entries will be removed.  This action cannot be undone.")
        dlg.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        dlg.setDefaultButton(QtGui.QMessageBox.No)
        ret = dlg.exec_()
        if ret == QtGui.QMessageBox.Yes:
            self._app.playlist.generate_default_playlist()
            self.update_playlist()

    def on_settings_networking(self):
        DlgSetupNetworking(self).exec_()

