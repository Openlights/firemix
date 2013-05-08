import threading
import logging
import inspect

import presets
from core.mixer import Mixer
from core.networking import Networking
from core.scene_loader import SceneLoader
from lib.playlist import Playlist


log = logging.getLogger("firemix")

class FireMixApp(threading.Thread):
    """
    Main logic of FireMix.  Operates the mixer tick loop.
    """

    def __init__(self, args):
        self._running = False
        self._net = Networking()
        self._scene = SceneLoader(args.scene).load()
        self._playlist = Playlist(args.playlist)
        self._mixer = Mixer(self, net=self._net, scene=self._scene, enable_profiling=args.profile)

        log.info("Loading presets...")
        for name, obj in inspect.getmembers(presets, inspect.isclass):
            log.info("Loading preset %s" % name)
            self._mixer.add_preset(obj)

        if args.preset:
            log.info("Setting constant preset %s" % args.preset)
            self._mixer.set_constant_preset(args.preset)

        log.info("The current preset is %s" % self._mixer.get_active_preset_name())

        threading.Thread.__init__(self)

    def run(self):
        self._running = True
        self._mixer.run()

    def stop(self):
        self._running = False
        self._playlist.save_file()