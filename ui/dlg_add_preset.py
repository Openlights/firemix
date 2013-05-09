from PySide import QtCore, QtGui

from ui.ui_dlg_add_preset import Ui_DlgAddPreset


class DlgAddPreset(QtGui.QDialog, Ui_DlgAddPreset):

    def __init__(self, parent=None):
        super(DlgAddPreset, self).__init__(parent)
        self.playlist = parent._app.playlist
        self.setupUi(self)

        # Populate preset list
        classes = self.playlist.get_available_presets()
        self.cb_preset_type.addItems(classes)
        self.cb_preset_type.currentIndexChanged.connect(self.populate_preset_name)
        self.edit_preset_name.textChanged.connect(self.validate_preset_name)
        self.populate_preset_name()

    def populate_preset_name(self):
        self.edit_preset_name.setText(self.playlist.suggest_preset_name(self.cb_preset_type.currentText()))

    def validate_preset_name(self):
        if self.playlist.preset_name_exists(self.edit_preset_name.text()):
            self.edit_preset_name.setStyleSheet("QLineEdit{background: #fdd;}")
            return False
        else:
            self.edit_preset_name.setStyleSheet("QLineEdit{background: #fff;}")
            return True

    def accept(self):
        if self.validate_preset_name():
            QtGui.QDialog.accept(self)
