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


from __future__ import print_function

from PyQt5 import QtCore, QtWidgets


class PresetListDelegate(QtWidgets.QStyledItemDelegate):

    def sizeHint(self, option, index):
        return QtCore.QSize(200, 20)

    def paint(self, painter, option, index):
        print(option.state)
        font = QtWidgets.QFont("Sans", 11, QtWidgets.QFont.Normal)
        if option.state == QtWidgets.QStyle.State_Selected:
            print("selected")
            font.setStyle(QtWidgets.QFont.Bold)
        r = option.rect
        align = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft | QtCore.Qt.TextWordWrap
        painter.setFont(font)
        painter.drawText(r.left(), r.top(), r.width(), r.height(), align, index.data())
