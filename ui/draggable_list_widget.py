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

from PyQt5 import QtCore, QtWidgets, QtWidgets


class DraggableListWidget(QtWidgets.QListWidget):
    """
    This custom QListWidget implements a signal to notify when a drag/drop has
    reordered the list elements.
    """

    layout_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtWidgets.QListWidget.__init__(self, parent)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.installEventFilter(self)

    def eventFilter(self, sender, event):
        if (event.type() == QtCore.QEvent.ChildRemoved):
            self.layout_changed.emit()
        return False
