from PySide.QtGui import QMainWindow, QPushButton, QMessageBox

from ui.ui_firemix import Ui_FireMixMain

class FireMixGUI(QMainWindow, Ui_FireMixMain):

    def __init__(self, parent=None, mixer=None):
        super(FireMixGUI, self).__init__(parent)
        self._mixer = mixer
        self.setupUi(self)
        self.btn_blackout.clicked.connect(self.on_btn_blackout)
        self.btn_runfreeze.clicked.connect(self.on_btn_runfreeze)
        self.btn_playpause.clicked.connect(self.on_btn_playpause)
        self.btn_next_preset.clicked.connect(self.on_btn_next_preset)
        self.btn_prev_preset.clicked.connect(self.on_btn_prev_preset)

    def closeEvent(self, event):
        self._mixer.stop()
        event.accept()

    def on_btn_blackout(self):
        pass

    def on_btn_playpause(self):
        if self._mixer.is_paused():
            self._mixer.pause(False)
            self.btn_playpause.setText("Pause")
        else:
            self._mixer.pause()
            self.btn_playpause.setText("Play")

    def on_btn_runfreeze(self):
        if self._mixer.is_frozen():
            self._mixer.freeze(False)
            self.btn_runfreeze.setText("Freeze")
        else:
            self._mixer.freeze()
            self.btn_runfreeze.setText("Unfreeze")

    def on_btn_next_preset(self):
        pass

    def on_btn_prev_preset(self):
        pass
