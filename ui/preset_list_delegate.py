from PySide import QtCore, QtGui


class PresetListDelegate(QtGui.QStyledItemDelegate):

    def sizeHint(self, option, index):
        return QtCore.QSize(200, 20)

    def paint(self, painter, option, index):
        print option.state
        font = QtGui.QFont("Sans", 11, QtGui.QFont.Normal)
        if option.state == QtGui.QStyle.State_Selected:
            print "selected"
            font.setStyle(QtGui.QFont.Bold)
        r = option.rect
        align = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft | QtCore.Qt.TextWordWrap
        painter.setFont(font)
        painter.drawText(r.left(), r.top(), r.width(), r.height(), align, index.data())