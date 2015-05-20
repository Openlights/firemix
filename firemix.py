# This file is part of Firemix.
#
# Copyright 2013-2015 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

import sys
import logging
import argparse
import signal

from PySide import QtGui

from firemix_app import FireMixApp
from ui.firemixgui import FireMixGUI


def sig_handler(sig, frame):
    global app
    app.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    log = logging.getLogger("firemix")

    signal.signal(signal.SIGINT, sig_handler)

    parser = argparse.ArgumentParser(description="Firelight mixer and preset host")
    parser.add_argument("scene", type=str, help="Scene file to load (create scenes with FireSim)")
    parser.add_argument("--playlist", type=str, help="Playlist file to load", default=None)
    parser.add_argument("--profile", action='store_const', const=True, default=False, help="Enable profiling")
    parser.add_argument("--yappi", action='store_const', const=True, default=False, help="Enable YAPPI")
    parser.add_argument("--nogui", action='store_const', const=True, default=False, help="Disable GUI")
    parser.add_argument("--preset", type=str, help="Specify a preset name to run only that preset (useful for debugging)")
    parser.add_argument("--verbose", action='store_const', const=True, default=False, help="Enable verbose log output")
    parser.add_argument("--noaudio", action='store_const', const=True, default=False, help="Disable audio processing client")

    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    log.info("Booting FireMix...")

    qt_app = QtGui.QApplication(sys.argv)

    app = FireMixApp(args, parent=qt_app)
    app.start()

    if not args.nogui:
        gui = FireMixGUI(app=app)
        gui.show()

    qt_app.exec_()

    if args.profile:
        print   "------ TICK TIME HISTOGRAM ------"
        elapsed = (app.mixer._stop_time - app.mixer._start_time)
        print "%d frames in %0.2f seconds (%0.2f FPS) " %  (app.mixer._num_frames, elapsed, app.mixer._num_frames / elapsed)
        for c in sorted(app.mixer._tick_time_data.iterkeys()):
            print "[%d fps]:\t%4d\t%0.2f%%" % (c, app.mixer._tick_time_data[c], (float(app.mixer._tick_time_data[c]) / app.mixer._num_frames) * 100.0)
