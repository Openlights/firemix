import logging
import inspect
import signal
import argparse
import yappi

import presets
from core.mixer import Mixer
from core.networking import Networking
from core.scene_loader import SceneLoader


def sigint_handler(signum, frame):
    global mixer
    mixer.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("firemix")

    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGABRT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)

    parser = argparse.ArgumentParser(description="Firelight mixer and preset host")
    parser.add_argument("scene", type=str, help="Scene file to load (create scenes with FireSim)")
    parser.add_argument("--profile", action='store_const', const=True, default=False, help="Enable profiling")
    parser.add_argument("--preset", type=str, help="Specify a preset name to run only that preset (useful for debugging)")

    args = parser.parse_args()

    log.info("Booting FireMix...")

    net = Networking()

    scene = SceneLoader("data/scenes/%s" % args.scene).load()
    log.info("Loaded scene from %s", scene._data["filepath"])

    mixer = Mixer(net=net, scene=scene, enable_profiling=args.profile)

    log.info("Loading presets...")
    for name, obj in inspect.getmembers(presets, inspect.isclass):
        log.info("Loading preset %s" % name)
        mixer.add_preset(obj)

    if args.preset != "":
        log.info("Setting constant preset %s" % args.preset)
        mixer.set_constant_preset(args.preset)

    log.info("The current preset is %s" % mixer.get_active_preset_name())

    if args.profile:
        log.info("Starting profiler")
        yappi.start()
    mixer.run()

    while mixer._running:
        pass

    if args.profile:
        stats = yappi.get_stats(yappi.SORTTYPE_TSUB, yappi.SORTORDER_DESC, 10)
        stats = [(s.name, s.ttot) for s in stats.func_stats]
        print "\n------ PROFILING STATS ------"
        for s in stats:
            print "%s\t[%0.3f]" % (s[0], s[1])
        print   "------ TICK TIME HISTOGRAM ------"
        elapsed = (mixer._stop_time - mixer._start_time)
        print "%d frames in %0.2f seconds (%0.2f FPS) " %  (mixer._num_frames, elapsed, mixer._num_frames / elapsed)
        for c in sorted(mixer._tick_time_data.iterkeys()):
            print "[%d fps]:\t%4d\t%0.2f%%" % (c, mixer._tick_time_data[c], (float(mixer._tick_time_data[c]) / mixer._num_frames) * 100.0)
