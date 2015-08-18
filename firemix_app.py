# This file is part of Firemix.
#
# Copyright 2013-2015 Jonathan Evans <jon@craftyjon.com>
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


import logging

from PySide import QtCore

from core.mixer import Mixer
from core.networking import Networking
from core.scene_loader import SceneLoader
from core.rpc_server import RPCServer
from lib.playlist import Playlist
from lib.settings import Settings
from lib.scene import Scene
from lib.plugin_loader import PluginLoader
from lib.aubio_connector import AubioConnector
from lib.buffer_utils import BufferUtils


log = logging.getLogger("firemix")


class FireMixApp(QtCore.QThread):
    """
    Main logic of FireMix.  Operates the mixer tick loop.
    """
    playlist_changed = QtCore.Signal()

    def __init__(self, parent, args):
        QtCore.QThread.__init__(self, parent)
        self._running = False
        self.args = args
        self.settings = Settings()
        self.net = Networking(self)
        BufferUtils.set_app(self)
        self.scene = Scene(self)
        self.plugins = PluginLoader()
        self.mixer = Mixer(self)
        self.playlist = Playlist(self)
        self.qt_app = parent

        self.scene.warmup()

        self.aubio_connector = None
        if not self.args.noaudio:
            self.aubio_thread = QtCore.QThread()
            self.aubio_thread.start()
            self.aubio_connector = AubioConnector()
            self.aubio_connector.onset_detected.connect(self.mixer.onset_detected)
            self.aubio_connector.fft_data.connect(self.mixer.audio.update_fft_data)
            self.aubio_connector.pitch_data.connect(self.mixer.audio.update_pitch_data)
            self.aubio_connector.moveToThread(self.aubio_thread)

        self.mixer.set_playlist(self.playlist)

        if self.args.preset:
            log.info("Setting constant preset %s" % args.preset)
            self.mixer.set_constant_preset(args.preset)

        if self.args.rpc:
            log.info("RPC Server enabled")
            self.rpc_thread = QtCore.QThread()
            self.rpc_thread.start()
            self.rpc_server = RPCServer(firemix=self)
            self.rpc_server.moveToThread(self.rpc_thread)
            self.rpc_server.start.emit()

    def run(self):
        self._running = True
        self.mixer.run()

    def stop(self):
        self._running = False
        self.aubio_thread.quit()
        if self.rpc_server is not None:
            self.rpc_server.stop.emit()
            self.rpc_thread.quit()
            self.rpc_thread.wait(100)
        self.mixer.stop()
        self.playlist.save()
        self.settings.save()
