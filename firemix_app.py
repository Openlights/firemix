import threading
import logging
import inspect

import presets
from core.mixer import Mixer
from core.networking import Networking
from core.scene_loader import SceneLoader
from lib.playlist import Playlist
from lib.settings import Settings


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
        self.scene = SceneLoader(self).load()
        self.playlist = Playlist(self)
        self.mixer = Mixer(self)

        log.info("Loading presets...")
        for name, obj in inspect.getmembers(presets, inspect.isclass):
            log.info("Loading preset %s" % name)
            self.mixer.add_preset(obj)

        if self.args.preset:
            log.info("Setting constant preset %s" % args.preset)
            self.mixer.set_constant_preset(args.preset)

        log.info("The current preset is %s" % self.mixer.get_active_preset_name())

        threading.Thread.__init__(self)

    def run(self):
        self._running = True
        self.mixer.run()

    def stop(self):
        self._running = False
        self.playlist.save_file()