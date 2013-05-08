from PySide import QtCore, QtGui


class DraggableListWidget(QtGui.QListWidget):
    """
    This custom QListWidget implements a signal to notify when a drag/drop has
    reordered the list elements.
    """

    layout_changed = QtCore.Signal()

    def __init__(self, parent=None):
        QtGui.QListWidget.__init__(self, parent)
        self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.installEventFilter(self)

    def eventFilter(self, sender, event):
        if (event.type() == QtCore.QEvent.ChildRemoved):
            self.layout_changed.emit()
        return False
