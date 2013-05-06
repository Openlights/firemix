from PySide.QtGui import QMainWindow, QPushButton, QMessageBox

from ui.ui_firemix import Ui_FireMixMain

class FireMixGUI(QMainWindow, Ui_FireMixMain):

    def __init__(self, parent=None, mixer=None):
        super(FireMixGUI, self).__init__(parent)
        self._mixer = mixer
        self.setupUi(self)
        self.btn_blackout.clicked.connect(self.on_btn_blackout)
        self.btn_playpause.clicked.connect(self.on_btn_playpause)

    def on_btn_blackout(self):
        pass

    def on_btn_playpause(self):
        if self._mixer.is_paused():
            self._mixer.pause(False)
            self.btn_playpause.setText("Pause")
        else:
            self._mixer.pause()
            self.btn_playpause.setText("Play")
