import logging
import inspect

import presets
from core.mixer import Mixer
from core.networking import Networking
from core.scene_loader import SceneLoader


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("FireMix")

    log.info("Booting FireMix...")

    net = Networking()

    scene = SceneLoader("data/scenes/demo.json").load()
    log.info("Loaded scene from %s", scene._data["filepath"])

    mixer = Mixer(net=net)


    log.info("Loading presets...")
    for name, obj in inspect.getmembers(presets, inspect.isclass):
        log.info("Loading preset %s" % name)
        mixer.add_preset(obj)

    log.info("The current preset is %s" % mixer.get_active_preset_name())

    mixer.run()

    while True:
        pass
