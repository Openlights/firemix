import logging
import threading
import time
import numpy as np

from lib.commands import SetAll, SetStrand, SetFixture, SetPixel, commands_overlap, blend_commands
from lib.raw_preset import RawPreset


log = logging.getLogger("firemix.core.mixer")


class Mixer:
    """
    Mixer is the brains of FireMix.  It handles the playback of presets
    and the generation of the final command stream to send to the output
    device(s).
    """

    def __init__(self, app):
        self._app = app
        self._net = app.net
        self._playlist = None
        self._scene = app.scene
        self._tick_rate = self._app.settings.get('mixer')['tick-rate']
        self._in_transition = False
        self._start_transition = False
        self._transition_duration = self._app.settings.get('mixer')['transition-duration']
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
        self._paused = False
        self._frozen = False

        # Load transitions
        tn = self._app.settings.get('mixer')['transition']
        tl = [c for c in self._app.plugins.get('Transition') if c.__name__ == tn]
        self._transition = tl[0]()

        if not self._scene:
            log.warn("No scene assigned to mixer.  Preset rendering and transitions are disabled.")
            self._transition_duration = 0.0
            self._enable_rendering = False
        else:
            log.info("Initializing preset rendering buffer")
            fh = self._scene.fixture_hierarchy()
            for strand in fh:
                self._strand_keys.append(strand)

            (maxs, maxf, maxp) = self._scene.get_matrix_extents()
            log.info("Loaded scene with %d strands, will create array of %d fixtures by %d pixels." % (maxs, maxf, maxp))
            self._main_buffer = np.zeros((maxs, maxf, maxp, 3))
            self._secondary_buffer = np.zeros((maxs, maxf, maxp, 3))
            self._max_fixtures = maxf
            self._max_pixels = maxp

    def run(self):
        if not self._running:
            self._tick_timer = threading.Timer(1.0 / self._tick_rate, self.on_tick_timer)
            self._tick_timer.start()
            self._running = True
            self._elapsed = 0.0
            self._num_frames = 0
            self._start_time = self._last_frame_time = time.time()
            self.reset_output_buffer()

    def stop(self):
        self._running = False
        self._stop_time = time.time()

    def pause(self, pause=True):
        self._paused = pause

    def is_paused(self):
        return self._paused

    def freeze(self, freeze=True):
        self._frozen = freeze

    def is_frozen(self):
        return self._frozen

    def set_preset_duration(self, duration):
        if duration > self._transition_duration:
            self._duration = duration
        else:
            log.warn("Duration %f must be longer than the transition duration (%f)" % (duration, self._transition_duration))

    def get_preset_duration(self):
        return self._duration

    def set_transition_duration(self, duration):
        if duration >= 0.0:
            self._transition_duration = duration
        else:
            log.warn("Transition duration must be positive or zero.")

    def get_transition_duration(self):
        return self._transition_duration

    def on_tick_timer(self):
        if self._frozen:
            delay = 1.0 / self._tick_rate
        else:
            start = time.clock()
            self.tick()
            dt = (time.clock() - start)
            delay = max(0, (1.0 / self._tick_rate) - dt)
            self._elapsed += (1.0 / self._tick_rate)
        self._running = self._app._running
        if self._running:
            self._tick_timer = threading.Timer(delay, self.on_tick_timer)
            self._tick_timer.start()

    def set_constant_preset(self, preset_name):
        self._playlist.set_active_preset_by_name(preset_name)
        self._paused = True

    def set_playlist(self, playlist):
        """
        Assigns a Playlist object to the mixer
        """
        self._playlist = playlist

    def get_tick_rate(self):
        return self._tick_rate

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
        #TODO: Fix this after the Playlist merge
        self._in_transition = True
        self._start_transition = True
        self._elapsed = 0.0

    def tick(self):
        self._num_frames += 1
        if len(self._playlist) > 0:

            self._playlist.get_active_preset().clear_commands()
            self._playlist.get_active_preset().tick()
            transition_progress = 0.0

            # Handle transition by rendering both the active and the next preset, and blending them together
            if self._in_transition:
                if self._start_transition:
                    self._start_transition = False
                    self._playlist.get_next_preset()._reset()
                    self._secondary_buffer = np.zeros((len(self._strand_keys), self._max_fixtures, self._max_pixels, 3))
                if self._transition_duration > 0.0:
                    transition_progress = self._elapsed / self._transition_duration
                else:
                    transition_progress = 1.0
                self._playlist.get_next_preset().clear_commands()
                self._playlist.get_next_preset().tick()

                # Exit from transition state after the transition duration has elapsed
                if transition_progress >= 1.0:
                    self._in_transition = False
                    # Reset the elapsed time counter so the preset runs for the full duration after the transition
                    self._elapsed = 0.0
                    self._playlist.advance()

            # If the scene tree is available, we can do efficient mixing of presets.
            # If not, a tree would need to be constructed on-the-fly.
            # TODO: Support mixing without a scene tree available
            if self._enable_rendering:
                if self._in_transition:
                    self.render_presets(self._playlist.get_active_index(), self._playlist.get_next_index(), transition_progress)
                else:
                    self.render_presets(self._playlist.get_active_index())
            else:
                if self._net is not None:
                    self._net.write(self._playlist.get_active_preset().get_commands_packed())

            if not self._paused and (self._elapsed >= self._duration) and self._playlist.get_active_preset().can_transition():
                if len(self._playlist) > 1:
                    self.start_transition()
                self._elapsed = 0.0

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
        else:
            commands = self._playlist.get_preset_by_index(first).get_commands()
            #print commands
            self.render_command_list(commands, self._main_buffer)

        if self._enable_profiling:
            dt = 1000.0 * (time.time() - start)
            if dt > 10.0:
                log.info("rendered first preset in %0.2f ms (%d commands)" % (dt, len(commands)))

        if second is not None:
            if self._enable_profiling:
                start = time.time()

            if isinstance(self._playlist.get_preset_by_index(second), RawPreset):
                self._secondary_buffer = self._playlist.get_preset_by_index(second).get_buffer()
            else:
                second_commands = self._playlist.get_preset_by_index(second).get_commands()
                self.render_command_list(second_commands, self._secondary_buffer)

            if self._enable_profiling:
                dt = 1000.0 * (time.time() - start)
                if dt > 10.0:
                    log.info("rendered second preset in %0.2f ms (%d commands)" % (dt, len(second_commands)))

            if self._in_transition:
                self._main_buffer = self._transition.get(self._main_buffer, self._secondary_buffer, transition_progress)

        if self._net is not None:
            data = dict()
            for k, v in enumerate(self._strand_keys):
                data[v] = self.get_strand_data(k, v)
            self._net.write_strand(data)

    def get_strand_data(self, strand_key, strand_id):
        """
        Returns an optimized list of strand data, in fixture order, using the scene map
        """
        len_strand = sum([fix.pixels() for fix in self._scene.fixtures() if fix.strand() == strand_id])
        data = self._main_buffer[strand_key].astype(int).tolist()
        data_flat = [item for sublist in data for item in sublist]
        data_flat = [item for sublist in data_flat for item in sublist]
        return data_flat[0:3 * len_strand]

    def reset_output_buffer(self):
        """
        Clears the output buffer
        """
        self._main_buffer = np.zeros((len(self._strand_keys), self._max_fixtures, self._max_pixels, 3))
        self._secondary_buffer = np.zeros((len(self._strand_keys), self._max_fixtures, self._max_pixels, 3))

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
                buffer[:,:,:] = color

            elif isinstance(command, SetStrand):
                strand = command.get_strand()
                buffer[strand,:,:] = color

            elif isinstance(command, SetFixture):
                strand = command.get_strand()
                address = command.get_address()
                buffer[strand,address,:] = color

            elif isinstance(command, SetPixel):
                strand = command.get_strand()
                address = command.get_address()
                pixel = command.get_pixel()
                buffer[strand][address][pixel] = color
