# This file is part of Firemix.
#
# Copyright 2013-2016 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Firemix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Firemix.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import functools
import logging
import signal
import sys

from PySide import QtCore, QtGui

try:
    import qdarkstyle
except ImportError:
    qdarkstyle = None

from firemix_app import FireMixApp
from ui.firemixgui import FireMixGUI


def call_ignoring_exceptions(func):
    try:
        func()
    except Exception as e:
        logging.getLogger("firemix").exception("Ignoring exception during shutdown request")

def sig_handler(app, sig, frame):
    logging.getLogger("firemix").info("Received signal %d.  Shutting down.", sig)
    call_ignoring_exceptions(app.stop)
    call_ignoring_exceptions(app.exit)
    call_ignoring_exceptions(app.qt_app.exit)

def main():
    logging.basicConfig(level=logging.ERROR)
    log = logging.getLogger("firemix")

    parser = argparse.ArgumentParser(description="Firelight mixer and preset host")
    parser.add_argument("scene", type=str, help="Scene file to load (create scenes with FireSim)")
    parser.add_argument("--playlist", type=str, help="Playlist file to load", default=None)
    parser.add_argument("--profile", action='store_const', const=True, default=False, help="Enable profiling")
    parser.add_argument("--yappi", action='store_const', const=True, default=False, help="Enable YAPPI")
    parser.add_argument("--nogui", dest='gui', action='store_false',
                        default=True, help="Disable GUI")
    parser.add_argument("--preset", type=str, help="Specify a preset name to run only that preset (useful for debugging)")
    parser.add_argument("--verbose", "-v", action='count', help="Enable verbose log output. Specify more than once for more output")
    parser.add_argument("--noaudio", action='store_const', const=True, default=False, help="Disable audio processing client")

    args = parser.parse_args()

    if args.verbose >= 2:
        log.setLevel(logging.DEBUG)
    elif args.verbose >= 1:
        log.setLevel(logging.INFO)

    log.info("Booting FireMix...")

    qt_app = QtGui.QApplication(sys.argv, args.gui)
    qt_app.setStyleSheet(qdarkstyle.load_stylesheet())
    app = FireMixApp(qt_app, args)

    signal.signal(signal.SIGINT, functools.partial(sig_handler, app))

    app.start()

    if args.gui:
        gui = FireMixGUI(app=app)
        app.gui = gui
        gui.show()
    else:
        # When the UI isn't running, the Qt application spends all its time
        # running in its event loop (implemented in C).  During that time, we
        # can't process any (Unix) signals in Python.  So, in order to handle
        # signals, we have to occationally execute some Python code.  We just do
        # nothing when the timeout fires.
        timer = QtCore.QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)

    qt_app.exec_()

    if args.profile:
        print   "------ TICK TIME HISTOGRAM ------"
        elapsed = (app.mixer._stop_time - app.mixer._start_time)
        print "%d frames in %0.2f seconds (%0.2f FPS) " %  (app.mixer._num_frames, elapsed, app.mixer._num_frames / elapsed)
        for c in sorted(app.mixer._tick_time_data.iterkeys()):
            print "[%d fps]:\t%4d\t%0.2f%%" % (c, app.mixer._tick_time_data[c], (float(app.mixer._tick_time_data[c]) / app.mixer._num_frames) * 100.0)

if __name__ == "__main__":
    main()
