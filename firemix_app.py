import logging

from PySide import QtCore

from core.mixer import Mixer
from core.networking import Networking
from core.scene_loader import SceneLoader
from lib.playlist import Playlist
from lib.settings import Settings
from lib.scene import Scene
from lib.plugin_loader import PluginLoader
from lib.aubio_connector import AubioConnector
from lib.buffer_utils import BufferUtils


log = logging.getLogger("firemix")


class FireMixApp(QtCore.QThread):
    """
    Main logic of FireMix.  Operates the mixer tick loop.
    """
    playlist_changed = QtCore.Signal()

    def __init__(self, args, parent=None):
        self._running = False
        self.args = args
        self.settings = Settings()
        self.net = Networking(self)
        BufferUtils.set_app(self)
        self.scene = Scene(self)
        self.plugins = PluginLoader()
        self.mixer = Mixer(self)
        self.playlist = Playlist(self)

        self.scene.warmup()

        self.aubio_connector = None
        if self.args.audio:
            self.aubio_connector = AubioConnector()
            self.aubio_connector.onset_detected.connect(self.mixer.onset_detected)

        self.mixer.set_playlist(self.playlist)

        if self.args.preset:
            log.info("Setting constant preset %s" % args.preset)
            self.mixer.set_constant_preset(args.preset)

        QtCore.QThread.__init__(self, parent)

    def run(self):
        self._running = True
        self.mixer.run()

    def stop(self):
        self._running = False
        self.mixer.stop()
        self.playlist.save()
        self.settings.save()