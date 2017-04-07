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


import logging
import threading
import time

from PySide import QtCore

from core.mixer import Mixer
from core.networking import Networking
from core.scene_loader import SceneLoader
from lib.playlist import Playlist
from lib.settings import Settings
from lib.scene import Scene
from lib.plugin_loader import PluginLoader
from lib.aubio_connector import AubioConnector
from lib.buffer_utils import BufferUtils


log = logging.getLogger("firemix")


class FireMixApp(QtCore.QObject):
    """
    Main logic of FireMix.  Operates the mixer tick loop.
    """
    playlist_changed = QtCore.Signal()

    def __init__(self, parent, args):
        super(FireMixApp, self).__init__()
        self._running = False
        self.args = args
        self.settings = Settings()
        self.net = Networking(self)
        BufferUtils.set_app(self)
        self.scene = Scene(self)
        self.plugins = PluginLoader()
        self.mixer = Mixer(self)
        self.playlist = Playlist(self)

        # TODO: The tick rate probably shouldn't be a mixer setting any more
        self._tick_rate = self.settings.get('mixer')['tick-rate']
        self._last_tick_time = 0.0
        self._render_thread = None
        self._timer_thread = None

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

    def start(self):
        assert not self._running, "Cannot start FireMixApp more than once"
        self._running = True
        self.mixer.start()

        self._last_tick_time = 1.0 / self._tick_rate
        self._render_thread = threading.Thread(target=self._render_loop,
                                               name="Firemix-render-thread")
        self._render_thread.start()

    def stop(self):
        self._running = False

        self._render_thread.join()
        self._render_thread = None

        self.aubio_thread.quit()
        self.mixer.stop()
        self.playlist.save()
        self.settings["last-preset"] = self.playlist.active_preset.name()
        self.settings.save()

    def _render_loop(self):
        delay = 0.0
        while self._running:
            time.sleep(delay)
            if self.mixer._frozen:
                delay = 1.0 / self._tick_rate
            else:
                start = time.time()
                self.mixer.tick(self._last_tick_time)
                dt = (time.time() - start)
                delay = max(0, (1.0 / self._tick_rate) - dt)
                if not self.mixer._paused:
                    self.mixer._elapsed += dt + delay
