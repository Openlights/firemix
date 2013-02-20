import logging as log
import threading

from core.mixer import Mixer
from core.networking import Networking


def on_timer():
    global mixer
    mixer.tick()
    threading.Timer(1 / mixer.tick_rate, on_timer).start()

if __name__ == "__main__":
    log.basicConfig(level=log.DEBUG)
    log.info("Booting FireMix...")

    net = Networking()
    mixer = Mixer(net=net)
    threading.Timer(1 / mixer.tick_rate, on_timer).start()

    while True:
        pass
