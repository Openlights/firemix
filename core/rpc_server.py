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


import falcon
import json
import logging
from PyQt5.QtCore import pyqtSlot
from PySide import QtCore
from wsgiref import simple_server

log = logging.getLogger("firemix.rpc_server")

class SettingsResource:
    def __init__(self, firemix):
        self.firemix = firemix

    def on_get(self, req, resp):

        settings = {
            "dimmer": self.firemix.mixer.global_dimmer,
            "speed": self.firemix.mixer.global_speed,
            "intensity_mode": self.firemix.intensity_mode,
            "current_preset": self.firemix.playlist.active_preset.name(),
            "all_presets": [p.name() for p in self.firemix.playlist.get()]
        }

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(settings, indent=2)


# TODO: Use something other than simple_server that works better with threading

class RPCServer(QtCore.QObject):

    start = QtCore.Signal()
    stop = QtCore.Signal()

    def __init__(self, firemix, host='0.0.0.0', port=8000):
        QtCore.QObject.__init__(self)
        self.app = falcon.API()
        self.firemix = firemix
        self.host = host
        self.port = port
        self.start.connect(self.run)
        self.stop.connect(self.shutdown)

        self.init_app()

    def init_app(self):
        self.settings = SettingsResource(self.firemix)
        self.app.add_route('/settings', self.settings)

    @pyqtSlot()
    def run(self):
        log.info("RPC server listening at %s:%d" % (self.host, self.port))
        self.server = simple_server.make_server(self.host, self.port, self.app)
        self._running = True

        while self._running:
            self.server.handle_request()

        self.server.shutdown()

    @pyqtSlot()
    def shutdown(self):
        self._running = False
        log.info("Shutting down RPC server")
        self.server.shutdown()
