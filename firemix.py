import logging as log
import inspect

import presets
from core.mixer import Mixer
from core.networking import Networking


if __name__ == "__main__":
    log.basicConfig(level=log.DEBUG)
    log.info("Booting FireMix...")

    net = Networking()
    mixer = Mixer(net=net)

    log.info("Loading presets...")
    for name, obj in inspect.getmembers(presets, inspect.isclass):
        log.info("Loading preset %s" % name)
        mixer.add_preset(obj)

    log.info("The current preset is %s" % mixer.get_active_preset_name())

    mixer.run()

    while True:
        pass
