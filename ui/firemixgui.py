from PySide import QtGui, QtCore

from lib.parameters import BoolParameter, FloatParameter, IntParameter, RGBParameter

from ui.ui_firemix import Ui_FireMixMain


class FireMixGUI(QtGui.QMainWindow, Ui_FireMixMain):

    def __init__(self, parent=None, mixer=None):
        super(FireMixGUI, self).__init__(parent)
        self._mixer = mixer
        self.setupUi(self)

        # Control
        self.btn_blackout.clicked.connect(self.on_btn_blackout)
        self.btn_runfreeze.clicked.connect(self.on_btn_runfreeze)
        self.btn_playpause.clicked.connect(self.on_btn_playpause)
        self.btn_next_preset.clicked.connect(self.on_btn_next_preset)
        self.btn_prev_preset.clicked.connect(self.on_btn_prev_preset)

        # File menu
        self.action_file_load_scene.triggered.connect(self.on_file_load_scene)
        self.action_file_reload_presets.triggered.connect(self.on_file_reload_presets)
        self.action_file_quit.triggered.connect(self.close)

        # Preset list
        self.lst_presets.itemDoubleClicked.connect(self.on_preset_double_clicked)

        # Settings
        self.edit_preset_duration.valueChanged.connect(self.on_preset_duration_changed)
        self.edit_transition_duration.valueChanged.connect(self.on_transition_duration_changed)
        self.cb_transition_mode.currentIndexChanged.connect(self.on_transition_mode_changed)

        # Preset Parameters
        self.tbl_preset_parameters.itemChanged.connect(self.on_preset_parameter_changed)

        self.update_preset_list()
        self.load_preset_parameters_table()
        self.tbl_preset_parameters.setDisabled(True)
        self._mixer.set_preset_changed_callback(self.on_mixer_preset_changed)

    def closeEvent(self, event):
        self._mixer.stop()
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
        self._mixer.next()

    def on_btn_prev_preset(self):
        self._mixer.prev()

    def update_preset_list(self):
        self.lst_presets.clear()
        presets = self._mixer.get_preset_playlist()
        current = self._mixer.get_active_preset()
        for preset in presets:
            item = QtGui.QListWidgetItem(preset.__class__.__name__)

            if preset == current:
                item.setBackground(QtGui.QColor(100, 255, 200))
            self.lst_presets.addItem(item)

    def on_mixer_preset_changed(self, new_preset):
        self.update_preset_list()
        self.load_preset_parameters_table()

    def on_file_load_scene(self):
        pass

    def on_file_reload_presets(self):
        pass

    def on_preset_double_clicked(self, preset_item):
        self._mixer.set_active_preset_by_name(preset_item.text())

    def on_preset_duration_changed(self):
        nd = self.edit_preset_duration.value()
        self._mixer.set_preset_duration(nd)
        self.edit_preset_duration.setValue(self._mixer.get_preset_duration())

    def on_transition_duration_changed(self):
        nd = self.edit_transition_duration.value()
        self._mixer.set_transition_duration(nd)
        self.edit_transition_duration.setValue(self._mixer.get_transition_duration())

    def on_transition_mode_changed(self):
        pass

    def load_preset_parameters_table(self):
        self.tbl_preset_parameters.clear()

        parameters = self._mixer.get_active_preset().get_parameters()
        self.tbl_preset_parameters.setColumnCount(2)
        self.tbl_preset_parameters.setRowCount(len(parameters))
        for i, parameter in enumerate(parameters):
            key_item = QtGui.QTableWidgetItem(str(parameter))
            key_item.setFlags(QtCore.Qt.ItemIsEnabled)
            value_item = QtGui.QTableWidgetItem(str(parameter.get()))
            self.tbl_preset_parameters.setItem(i, 0, key_item)
            self.tbl_preset_parameters.setItem(i, 1, value_item)

        self.tbl_preset_parameters.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.tbl_preset_parameters.horizontalHeader().resizeSection(1, 125)

    def on_preset_parameter_changed(self, item):
        if item.column() == 0:
            return
        key = self.tbl_preset_parameters.item(item.row(), 0)
        par = self._mixer.get_active_preset().parameter(key.text())
        try:
            par.set_from_str(item.text())
            item.setText(par.get_as_str())
        except ValueError:
            item.setText(par.get_as_str())
