import threading
import logging

from core.mixer import Mixer
from core.networking import Networking
from core.scene_loader import SceneLoader
from lib.playlist import Playlist
from lib.settings import Settings
from lib.scene import Scene


log = logging.getLogger("firemix")


class FireMixApp(threading.Thread):
    """
    Main logic of FireMix.  Operates the mixer tick loop.
    """

    def __init__(self, args):
        self._running = False
        self.args = args
        self.settings = Settings()
        self.net = Networking(self)
        self.scene = Scene(SceneLoader(self))
        self.playlist = Playlist(self)
        self.mixer = Mixer(self)

        if self.args.preset:
            log.info("Setting constant preset %s" % args.preset)
            self.mixer.set_constant_preset(args.preset)

        threading.Thread.__init__(self)

    def run(self):
        self._running = True
        self.mixer.run()

    def stop(self):
        self._running = False
        self.playlist.save()
        self.settings.save()