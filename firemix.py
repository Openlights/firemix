import logging
import inspect
import signal
import sys
import yappi

import presets
from core.mixer import Mixer
from core.networking import Networking
from core.scene_loader import SceneLoader


ENABLE_PROFILING = True


def sigint_handler(signum, frame):
    global mixer
    mixer.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("firemix")

    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGABRT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)

    log.info("Booting FireMix...")

    net = Networking()

    scene = SceneLoader("data/scenes/demo.json").load()
    log.info("Loaded scene from %s", scene._data["filepath"])

    mixer = Mixer(net=net, scene=scene)


    log.info("Loading presets...")
    for name, obj in inspect.getmembers(presets, inspect.isclass):
        log.info("Loading preset %s" % name)
        mixer.add_preset(obj)

    log.info("The current preset is %s" % mixer.get_active_preset_name())

    if ENABLE_PROFILING:
        log.info("Starting profiler")
        yappi.start()
    mixer.run()

    while mixer._running:
        pass

    if ENABLE_PROFILING:
        stats = yappi.get_stats(yappi.SORTTYPE_TSUB, yappi.SORTORDER_DESC, 10)
        stats = [(s.name, s.ttot) for s in stats.func_stats]
        print "\n------ PROFILING STATS ------"
        for s in stats:
            print "%s\t[%0.3f]" % (s[0], s[1])
        print   "------ TICK TIME HISTOGRAM ------"
        elapsed = (mixer._stop_time - mixer._start_time)
        print "%d frames in %0.2f seconds (%0.2f FPS) " %  (mixer._num_frames, elapsed, mixer._num_frames / elapsed)
        for _, c in enumerate(mixer._tick_time_data):
            print "[%d fps]:\t%4d\t%0.2f%%" % (c, mixer._tick_time_data[c], (float(mixer._tick_time_data[c]) / mixer._num_frames) * 100.0)
