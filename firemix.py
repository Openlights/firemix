import logging
import argparse
import yappi
import signal

from core.rpc_server import RPCServer
from firemix_app import FireMixApp


def sig_handler(sig, frame):
    global app, rpc_server
    app.stop()
    rpc_server.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("firemix")

    signal.signal(signal.SIGINT, sig_handler)

    parser = argparse.ArgumentParser(description="Firelight mixer and preset host")
    parser.add_argument("scene", type=str, help="Scene file to load (create scenes with FireSim)")
    parser.add_argument("--playlist", type=str, help="Playlist file to load", default="default")
    parser.add_argument("--profile", action='store_const', const=True, default=False, help="Enable profiling")
    parser.add_argument("--preset", type=str, help="Specify a preset name to run only that preset (useful for debugging)")

    args = parser.parse_args()

    log.info("Booting FireMix...")

    if args.profile:
        log.info("Starting profiler")
        yappi.start()

    app = FireMixApp(args)
    rpc_server = RPCServer(app)

    try:
        app.start()
        rpc_server.start()
        app.join()
        rpc_server.join()
    except KeyboardInterrupt:
        log.info("Shutting down")

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
