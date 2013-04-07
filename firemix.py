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
    if ENABLE_PROFILING:
        stats = yappi.get_stats(yappi.SORTTYPE_TTOT, yappi.SORTORDER_DESC, 10)
        stats = [(s.name, s.ttot) for s in stats.func_stats]
        print "\n------ PROFILING STATS ------"
        for s in stats:
            print "%s\t[%0.3f]" % (s[0], s[1])
        print   "------ TICK TIME HISTOGRAM ------"
        print "Total frames: ", mixer._num_frames
        print "Elapsed time: %0.2f seconds" % (mixer._stop_time - mixer._start_time)
        for _, c in enumerate(mixer._tick_time_data):
            print "[%d fps]:\t%4d\t%0.2f%%" % (c, mixer._tick_time_data[c], (float(mixer._tick_time_data[c]) / mixer._num_frames) * 100.0)
    sys.exit(0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("FireMix")

    signal.signal(signal.SIGINT, sigint_handler)

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

    while True:
        pass
