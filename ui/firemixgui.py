from PySide.QtGui import QMainWindow, QPushButton, QMessageBox

from ui.ui_firemix import Ui_FireMixMain

class FireMixGUI(QMainWindow, Ui_FireMixMain):

    def __init__(self, parent=None):
        super(FireMixGUI, self).__init__(parent)
        self.setupUi(self)

