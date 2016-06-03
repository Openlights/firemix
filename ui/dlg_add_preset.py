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

from PySide import QtCore, QtGui

from ui.ui_dlg_add_preset import Ui_DlgAddPreset


class DlgAddPreset(QtGui.QDialog, Ui_DlgAddPreset):

    def __init__(self, parent=None):
        super(DlgAddPreset, self).__init__(parent)
        self.playlist = parent.app.playlist
        self.setupUi(self)

        # Populate preset list
        classes = self.playlist.get_available_patterns()
        self.cb_preset_type.addItems(classes)
        self.cb_preset_type.currentIndexChanged.connect(self.populate_preset_name)

        # TODO: This functionality shouldn't be in playlist -- maybe a preset loader?
        self.cb_existing_preset_name.addItems(self.playlist.get_all_preset_names())

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
        if self.tabWidget.currentIndex() == 1 or self.validate_preset_name():
            QtGui.QDialog.accept(self)
