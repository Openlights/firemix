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

from PySide import QtCore

from lib.commands import SetAll, SetStrand, SetFixture, SetPixel, commands_overlap, blend_commands
from lib.raw_preset import RawPreset
from lib.buffer_utils import BufferUtils


log = logging.getLogger("firemix.core.mixer")


class Mixer(QtCore.QObject):
    """
    Mixer is the brains of FireMix.  It handles the playback of presets
    and the generation of the final command stream to send to the output
    device(s).
    """
    transition_starting = QtCore.Signal()

    def __init__(self, app):
        super(Mixer, self).__init__()
        self._app = app
        self._net = app.net
        self._playlist = None
        self._scene = app.scene
        self._tick_rate = self._app.settings.get('mixer')['tick-rate']
        self._in_transition = False
        self._start_transition = False
        self._transition_duration = self._app.settings.get('mixer')['transition-duration']
        self._transition_slop = self._app.settings.get('mixer')['transition-slop']
        self._tick_timer = None
        self._duration = self._app.settings.get('mixer')['preset-duration']
        self._elapsed = 0.0
        self._running = False
        self._enable_rendering = True
        self._main_buffer = None
        self._max_fixtures = 0
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
        self._global_dimmer = 1.0
        self._global_speed = 1.0
        self._render_in_progress = False
        self.transition_progress = 0.0

        if self._app.args.profile and USE_YAPPI:
            yappi.start()

        # Load transitions
        self.set_transition_mode(self._app.settings.get('mixer')['transition'])

        if not self._scene:
            log.warn("No scene assigned to mixer.  Preset rendering and transitions are disabled.")
            self._transition_duration = 0.0
            self._enable_rendering = False
        else:
            log.info("Warming up BufferUtils cache...")
            BufferUtils.init()
            log.info("Completed BufferUtils cache warmup")

            log.info("Initializing preset rendering buffer")
            fh = self._scene.fixture_hierarchy()
            for strand in fh:
                self._strand_keys.append(strand)

            (maxs, maxf, maxp) = self._scene.get_matrix_extents()

            self._main_buffer = BufferUtils.create_buffer()
            self._secondary_buffer = BufferUtils.create_buffer()
            self._max_fixtures = maxf
            self._max_pixels = maxp

    def run(self):
        if not self._running:
            self._tick_rate = self._app.settings.get('mixer')['tick-rate']
            self._tick_timer = threading.Timer(1.0 / self._tick_rate, self.on_tick_timer)
            self._tick_timer.start()
            self._running = True
            self._elapsed = 0.0
            self._num_frames = 0
            self._start_time = self._last_frame_time = time.time()
            self.reset_output_buffer()

    def stop(self):
        self._running = False
        self._tick_timer.cancel()
        self._stop_time = time.time()

        if self._app.args.profile and USE_YAPPI:
            yappi.print_stats(sort_type=yappi.SORTTYPE_TSUB, limit=15, thread_stats_on=False)

    def pause(self, pause=True):
        self._paused = pause
        self._app.settings.get('mixer')['paused'] = pause

    def is_paused(self):
        return self._paused

    @QtCore.Slot()
    def onset_detected(self):
        t = time.clock()
        if (t - self._last_onset_time) > self._onset_holdoff:
            self._last_onset_time = t
            self._onset = True

    def set_global_dimmer(self, dimmer):
        self._global_dimmer = dimmer

    def set_global_speed(self, speed):
        self._global_speed = speed

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
        if not self._in_transition:
            self._transition = self.get_transition_by_name(name)
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
            log.warn("Preset duration must be positive or zero.")
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

    def on_tick_timer(self):
        if self._frozen:
            delay = 1.0 / self._tick_rate
        else:
            start = time.clock()
            self._render_in_progress = True
            self.tick()
            self._render_in_progress = False
            #self._onset = False
            dt = (time.clock() - start)
            delay = max(0, (1.0 / self._tick_rate) - dt)
            if not self._paused:
                self._elapsed += (1.0 / self._tick_rate)
        self._running = self._app._running
        if self._running:
            self._tick_timer = threading.Timer(delay, self.on_tick_timer)
            self._tick_timer.start()

    def set_constant_preset(self, classname):
        self._app.playlist.clear_playlist()
        self._app.playlist.add_preset(classname, classname)
        self._paused = True

    def set_playlist(self, playlist):
        """
        Assigns a Playlist object to the mixer
        """
        self._playlist = playlist

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
        if len(self._playlist) == 0:
            return
        self.start_transition((self._playlist.get_active_index() + 1) % len(self._playlist))

    def prev(self):
        #TODO: Fix this after the Playlist merge
        if len(self._playlist) == 0:
            return
        self.start_transition((self._playlist.get_active_index() - 1) % len(self._playlist))

    def start_transition(self, next=None):
        """
        Starts a transition.  If a name is given for Next, it will be the endpoint of the transition
        """
        if next is not None:
            self._playlist.set_next_preset_by_name(next)

        self._in_transition = True
        self._start_transition = True
        self._elapsed = 0.0
        self.transition_starting.emit()

    def cancel_transition(self):
        self._start_transition = False
        if self._in_transition:
            self._in_transition = False

    def tick(self):
        self._num_frames += 1
        dt = (self._global_speed / self._tick_rate)
        if len(self._playlist) > 0:

            self._playlist.get_active_preset().clear_commands()
            self._playlist.get_active_preset().tick(dt)

            # Handle transition by rendering both the active and the next preset, and blending them together
            if self._in_transition:
                if self._start_transition:
                    self._start_transition = False
                    self.transition_progress
                    if self._app.settings.get('mixer')['transition'] == "Random":
                        self.get_next_transition()
                    if self._transition:
                        self._transition.reset()
                    self._playlist.get_next_preset()._reset()
                    self._secondary_buffer = BufferUtils.create_buffer()

                if self._transition_duration > 0.0 and self._transition is not None:
                    if not self._paused:
                        self.transition_progress = self._elapsed / self._transition_duration
                else:
                    self.transition_progress = 1.0
                self._playlist.get_next_preset().clear_commands()
                self._playlist.get_next_preset().tick(dt)

                # Exit from transition state after the transition duration has elapsed
                if self.transition_progress >= 1.0:
                    self._in_transition = False
                    # Reset the elapsed time counter so the preset runs for the full duration after the transition
                    self._elapsed = 0.0
                    self._playlist.advance()

            # If the scene tree is available, we can do efficient mixing of presets.
            # If not, a tree would need to be constructed on-the-fly.
            # TODO: Support mixing without a scene tree available
            if self._enable_rendering:
                if self._in_transition:
                    self.render_presets(self._playlist.get_active_index(), self._playlist.get_next_index(), self.transition_progress)
                else:
                    self.render_presets(self._playlist.get_active_index())
            else:
                if self._net is not None:
                    self._net.write(self._playlist.get_active_preset().get_commands_packed())

            if not self._paused and (self._elapsed >= self._duration) and self._playlist.get_active_preset().can_transition() and not self._in_transition:
                if (self._elapsed >= (self._duration + self._transition_slop)) or self._onset:
                    if len(self._playlist) > 1:
                        self.start_transition()
                    self._elapsed = 0.0

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

    def render_presets(self, first, second=None, transition_progress=0.0):
        """
        Grabs the command output from a preset with the index given by first.
        If a second preset index is given, render_preset will use a Transition class to generate the output
        according to transition_progress (0.0 = 100% first, 1.0 = 100% second)
        """

        if self._enable_profiling:
            start = time.time()

        commands = []

        if isinstance(self._playlist.get_preset_by_index(first), RawPreset):
            self._main_buffer = self._playlist.get_preset_by_index(first).get_buffer()
            if self._app.args.profile:
                for item in self._main_buffer.flat:
                    if math.isnan(item):
                        raise ValueError

        else:
            commands = self._playlist.get_preset_by_index(first).get_commands()
            self.render_command_list(commands, self._main_buffer)

        if second is not None:
            if self._enable_profiling:
                start = time.time()

            if isinstance(self._playlist.get_preset_by_index(second), RawPreset):
                self._secondary_buffer = self._playlist.get_preset_by_index(second).get_buffer()
                if self._app.args.profile:
                    for item in self._main_buffer.flat:
                        if math.isnan(item):
                            raise ValueError
            else:
                second_commands = self._playlist.get_preset_by_index(second).get_commands()
                self.render_command_list(second_commands, self._secondary_buffer)

            if self._in_transition:
                self._main_buffer = self._transition.get(self._main_buffer, self._secondary_buffer, transition_progress)
                if self._app.args.profile:
                    for item in self._main_buffer.flat:
                        if math.isnan(item):
                            raise ValueError

        if self._global_dimmer < 1.0:
            self._main_buffer *= (1.0, self._global_dimmer, 1.0)

        if self._net is not None:
            self._main_buffer.T[0] = np.mod(self._main_buffer.T[0], 1.0)
            np.clip(self._main_buffer.T[1], 0.0, 1.0, self._main_buffer.T[1])
            np.clip(self._main_buffer.T[2], 0.0, 1.0, self._main_buffer.T[2])
            self._net.write(self._main_buffer)

    def create_buffers(self):
        """
        Pixel buffers are 3D numpy arrays.  The axes are strand, pixel, and color.
        The "y" axis (pixel) is an expanded pixel address
        """

    def reset_output_buffer(self):
        """
        Clears the output buffer
        """
        self._main_buffer = BufferUtils.create_buffer()
        self._secondary_buffer = BufferUtils.create_buffer()

    def render_command_list(self, list, buffer):
        """
        Renders the output of a command list to the output buffer.
        Commands are rendered in FIFO overlap style.  Run the list through
        filter_and_sort_commands() beforehand.
        If the output buffer is not zero (black) at a command's target,
        the output will be additively blended according to the blend_state
        (0.0 = 100% original, 1.0 = 100% new)
        """
        for command in list:
            color = command.get_color()
            if isinstance(command, SetAll):
                buffer[:,:] = color

            elif isinstance(command, SetStrand):
                strand = command.get_strand()
                start, end = BufferUtils.get_strand_extents(strand)
                buffer[start:end] = color

            elif isinstance(command, SetFixture):
                strand = command.get_strand()
                fixture = command.get_address()
                start = BufferUtils.logical_to_index((strand, fixture, 0))
                end = start + self._scene.fixture(strand, fixture).pixels
                buffer[start:end] = color

            elif isinstance(command, SetPixel):
                strand = command.get_strand()
                fixture = command.get_address()
                offset = command.get_pixel()
                pixel = BufferUtils.logical_to_index((strand, fixture, offset))
                buffer[pixel] = color

    def get_buffer_shape(self):
        return self._main_buffer.shape
