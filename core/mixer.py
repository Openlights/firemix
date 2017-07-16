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
import random
import math
import numpy as np

USE_YAPPI = True
try:
    import yappi
except ImportError:
    USE_YAPPI = False

from PyQt5 import QtCore

from lib.pattern import Pattern
from lib.buffer_utils import BufferUtils, struct_flat
from core.audio import Audio
from lib.aubio_connector import AubioConnector
from lib.colors import clip


log = logging.getLogger("firemix.core.mixer")


class Mixer(QtCore.QObject):
    """
    Mixer is the brains of FireMix.  It handles the playback of presets
    and the generation of the final command stream to send to the output
    device(s).
    """
    transition_starting = QtCore.pyqtSignal()

    def __init__(self, app):
        super(Mixer, self).__init__()
        self._app = app
        self._net = app.net
        self.playlist = None
        self._scene = app.scene
        self._tick_rate = self._app.settings.get('mixer')['tick-rate']
        self._in_transition = False
        self._start_transition = False
        self._transition_scrubbing = False
        self._transition_duration = self._app.settings.get('mixer')['transition-duration']
        self._transition_slop = self._app.settings.get('mixer')['transition-slop']
        self._render_thread = None
        self._duration = self._app.settings.get('mixer')['preset-duration']
        self._elapsed = 0.0
        self.running = False
        self._max_pixels = 0
        self._tick_time_data = dict()
        self._num_frames = 0
        self._last_frame_time = 0.0
        self._start_time = 0.0
        self._stop_time = 0.0
        self._strand_keys = list()
        self._enable_profiling = self._app.args.profile
        self._paused = self._app.settings.get('mixer').get('paused', False)
        self._frozen = False
        self._last_onset_time = 0.0
        self._onset_holdoff = self._app.settings.get('mixer')['onset-holdoff']
        self._onset = False
        self._reset_onset = False
        self.global_dimmer = 1.0
        self.global_speed = 1.0
        self._render_in_progress = False
        self._last_tick_time = 0.0
        self._fps_time = 0.0
        self._fps_frames = 0
        self._fps = 0.0
        self.last_time = time.time()
        self.transition_progress = 0.0

        # TODO: bring back noaudio
        #if not self._app.args.noaudio:
        # TODO: harmonize on threading.Thread
        self._audio_thread = QtCore.QThread()
        self._audio_thread.start()
        self.aubio_connector = AubioConnector()
        self.audio = Audio(self)
        self.audio.onset.connect(self.onset_detected)
        self.aubio_connector.onset_detected.connect(self.audio.trigger_onset)
        self.aubio_connector.fft_data.connect(self.audio.fft_data_from_network)
        self.aubio_connector.pitch_data.connect(self.audio.update_pitch_data)
        self.aubio_connector.moveToThread(self._audio_thread)

        if self._app.args.yappi and USE_YAPPI:
            print "yappi start"
            yappi.start()

        log.info("Warming up BufferUtils cache...")
        BufferUtils.init()
        log.info("Completed BufferUtils cache warmup")

        # Load transitions
        self.set_transition_mode(self._app.settings.get('mixer')['transition'])

        log.info("Initializing preset rendering buffer")
        fh = self._scene.fixture_hierarchy()
        for strand in fh:
            self._strand_keys.append(strand)

        (maxs, maxp) = self._scene.get_matrix_extents()

        self._buffer_a = BufferUtils.create_buffer()
        self._buffer_b = BufferUtils.create_buffer()
        self._output_buffer = BufferUtils.create_buffer()
        self._max_pixels = maxp

    @QtCore.pyqtSlot()
    def start(self):
        assert self._render_thread is None, "Cannot start render thread more than once"
        self._tick_rate = self._app.settings.get('mixer')['tick-rate']
        self._last_tick_time = 1.0 / self._tick_rate
        self._elapsed = 0.0
        self._num_frames = 0
        self._start_time = self._last_frame_time = time.time()
        self.reset_output_buffers()
        self.running = True

        self._render_thread = threading.Thread(target=self._render_loop,
                                               name="Firemix-render-thread")
        self._render_thread.start()

    def _render_loop(self):
        delay = 0.0
        while self.running:
            time.sleep(delay)
            if self._frozen:
                delay = 1.0 / self._tick_rate
            else:
                start = time.time()
                self._render_in_progress = True
                self.tick(self._last_tick_time)
                self._render_in_progress = False
                dt = (time.time() - start)
                delay = max(0, (1.0 / self._tick_rate) - dt)
                if not self._paused:
                    self._elapsed += dt + delay

    @QtCore.pyqtSlot()
    def restart(self):
        self.stop()
        self.start()

    @QtCore.pyqtSlot()
    def stop(self):
        self.running = False
        self._stop_time = time.time()
        if self._render_thread is not None:
            self._render_thread.join()
            self._render_thread = None

        # TODO: Should we restart the audio thread on mixer restart?
        #self._audio_thread.quit()
        #self._audio_thread = None

        if self._app.args.yappi and USE_YAPPI:
            yappi.get_func_stats().print_all()

    def pause(self, pause=True):
        self._paused = pause
        self._app.settings.get('mixer')['paused'] = pause

    def is_paused(self):
        return self._paused

    def fps(self):
        if self.running and self._num_frames > self._fps_frames:
            delta_t = time.time() - self._fps_time
            if delta_t > 1.0:
                self._fps = (self._num_frames - self._fps_frames) / delta_t
                self._fps_frames = self._num_frames
                self._fps_time = time.time()
            return self._fps
        else:
            self._fps_frames = 0
            self._fps_time = time.time()
            return 0.0

    @QtCore.pyqtSlot()
    def onset_detected(self):
        t = time.time()
        if (t - self._last_onset_time) > self._onset_holdoff:
            self._last_onset_time = t
            self._onset = True

    def get_transition_by_name(self, name):
        if not name or name == "Cut":
            return None

        if name == "Random":
            self.build_random_transition_list()
            return self.get_next_transition()

        tl = [c for c in self._app.plugins.get('Transition') if str(c(None)) == name]

        if len(tl) == 1:
            return tl[0](self._app)
        else:
            log.error("Transition %s is not loaded!" % name)
            return None

    def set_transition_mode(self, name):
        #if not self._in_transition:
        #    self._transition = self.get_transition_by_name(name)
        self._transition = self.get_transition_by_name(name)
        if self._transition is not None:
            self._transition.reset()
        return True

    def build_random_transition_list(self):
        self._transition_list = [c for c in self._app.plugins.get('Transition')]
        random.shuffle(self._transition_list)

    def get_next_transition(self):
        if len(self._transition_list) == 0:
            self.build_random_transition_list()
        self._transition = self._transition_list.pop()(self._app)
        self._transition.setup()

    def freeze(self, freeze=True):
        self._frozen = freeze

    def is_frozen(self):
        return self._frozen

    def set_preset_duration(self, duration):
        if duration >= 0.0:
            self._duration = duration
            return True
        else:
            log.warn("Pattern duration must be positive or zero.")
            return False

    def get_preset_duration(self):
        return self._duration

    def set_transition_duration(self, duration):
        if duration >= 0.0:
            self._transition_duration = duration
            return True
        else:
            log.warn("Transition duration must be positive or zero.")
            return False

    def get_transition_duration(self):
        return self._transition_duration

    def set_constant_preset(self, classname):
        self._app.playlist.clear_playlist()
        self._app.playlist.add_preset(classname, classname)
        self._paused = True

    def set_playlist(self, playlist):
        """
        Assigns a Playlist object to the mixer
        """
        self.playlist = playlist

    def get_tick_rate(self):
        return self._tick_rate

    def is_onset(self):
        """
        Called by presets; resets after tick if called during tick
        """
        if self._onset:
            self._reset_onset = True
            return True
        return False

    def next(self):
        #TODO: Fix this after the Playlist merge
        if len(self.playlist) == 0:
            return

        self.start_transition(self.playlist.next_preset)

    def prev(self):
        # Disabling this because it's not very useful and complicates implementation.
        pass

    def start_transition(self, next=None):
        """
        Starts a transition.  If a name is given for Next, it will be the endpoint of the transition
        """
        if next is not None:
            self.playlist.set_next_preset_by_name(next)

        self._in_transition = True
        self._start_transition = True
        self._elapsed = 0.0
        self.transition_starting.emit()
        next_preset = self.playlist.get_next_preset()
        log.info("Starting transition to pattern '%s'" % (next_preset.name()))

    def cancel_transition(self):
        self._start_transition = False
        self._transition_scrubbing = False
        if self._in_transition:
            self._in_transition = False
            self.transition_progress = 0

    def scrub_transition(self, scrub_ratio):
        if not self.is_paused():
            return

        self._in_transition = True

        if not self._transition_scrubbing:
            self._start_transition = True
            self._transition_scrubbing = True

        self.transition_progress = scrub_ratio

    def cancel_scrub(self):
        self._transition_scrubbing = False

    def tick(self, dt):
        self._num_frames += 1

        dt *= self.global_speed

        if len(self.playlist) > 0:

            active_preset = self.playlist.get_active_preset()
            next_preset = self.playlist.get_next_preset()

            if active_preset is None:
                return

            try:
                active_preset.tick(dt)
            except:
                log.error("Exception raised in preset %s" % active_preset.name())
                self.playlist.disable_presets_by_class(active_preset.__class__.__name__)
                raise

            # Handle transition by rendering both the active and the next
            # preset, and blending them together
            if self._in_transition and next_preset and (next_preset != active_preset):
                if self._start_transition:
                    self._start_transition = False
                    if self._app.settings.get('mixer')['transition'] == "Random":
                        self.get_next_transition()
                    if self._transition:
                        self._transition.reset()
                    next_preset._reset()

                if self._transition_duration > 0.0 and self._transition is not None:
                    if not self._paused and not self._transition_scrubbing:
                        self.transition_progress = clip(0.0,
                                                        self._elapsed / self._transition_duration,
                                                        1.0)
                else:
                    if not self._transition_scrubbing:
                        self.transition_progress = 1.0

                next_preset.tick(dt)

            # If the scene tree is available, we can do efficient mixing of presets.
            # If not, a tree would need to be constructed on-the-fly.
            # TODO: Support mixing without a scene tree available

            if self._in_transition:
                self.render_presets(active_preset, next_preset,
                                    self._transition,
                                    self.transition_progress,
                                    check_for_nan=self._enable_profiling)
            else:
                self.render_presets(active_preset,
                                    check_for_nan=self._enable_profiling)


            # Mod hue by 1 (to allow wrap-around) and clamp lightness and
            # saturation to [0, 1].
            np.mod(self._output_buffer['hue'], 1.0, self._output_buffer['hue'])
            np.clip(self._output_buffer['light'], 0.0, 1.0, self._output_buffer['light'])
            np.clip(self._output_buffer['sat'], 0.0, 1.0, self._output_buffer['sat'])

            # Write this buffer to enabled clients.
            if self._net is not None:
                self._net.write_buffer(self._output_buffer)

            if (not self._paused and (self._elapsed >= self._duration)
                and active_preset.can_transition()
                and not self._in_transition):

                if (self._elapsed >= (self._duration + self._transition_slop)) or self._onset:
                    if len(self.playlist) > 1:
                        self.start_transition()
                    self._elapsed = 0.0

            elif self._in_transition:
                if not self._transition_scrubbing and (self.transition_progress >= 1.0):
                    self._in_transition = False
                    # Reset the elapsed time counter so the preset runs for the
                    # full duration after the transition
                    self._elapsed = 0.0
                    self.playlist.advance()

        if self._reset_onset:
            self._onset = False
            self._reset_onset = False

        if self._enable_profiling:
            tick_time = (time.time() - self._last_frame_time)
            self._last_frame_time = time.time()
            if tick_time > 0.0:
                index = int((1.0 / tick_time))
                self._tick_time_data[index] = self._tick_time_data.get(index, 0) + 1

    def scene(self):
        return self._scene

    def render_presets(self, first_preset, second_preset=None,
                       transition=None, transition_progress=0.0,
                       check_for_nan=False):
        """
        Generates the final output buffer from either a single preset or two
        presets and a Transition.
        """

        first_preset.render(self._buffer_a)
        if check_for_nan:
            self._validate_buffer(self._buffer_a)

        if transition is None:
            # Single preset
            self._output_buffer = self._buffer_a
            return

        # Two presets
        second_preset.render(self._buffer_b)
        if check_for_nan:
            self._validate_buffer(self._buffer_b)

        transition.render(self._buffer_a, self._buffer_b,
                          transition_progress, self._output_buffer)
        if check_for_nan:
            self._validate_buffer(self._output_buffer)

    def reset_output_buffers(self):
        """
        Clears the output buffers
        """
        self._buffer_a = BufferUtils.create_buffer()
        self._buffer_b = BufferUtils.create_buffer()
        self._output_buffer = BufferUtils.create_buffer()

    def _validate_buffer(self, buf):
        np.isnan(struct_flat(buf), self._nan_check_buf)
        if np.any(self._nan_check_buf):
            raise ValueError
