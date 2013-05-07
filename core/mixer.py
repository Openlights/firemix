import threading
import logging
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

    def __init__(self, net=None, scene=None, tick_rate=32.0, preset_duration=5.0, enable_profiling=False):
        self._presets = []
        self._net = net
        self._scene = scene
        self._tick_rate = tick_rate
        self._active_preset = 0
        self._next_preset = 1
        self._in_transition = False
        self._transition_duration = 1.25
        self._tick_timer = None
        self._duration = preset_duration
        self._elapsed = 0.0
        self._running = False
        self._enable_rendering = True
        self._output_buffer = None
        self._max_fixtures = 0
        self._max_pixels = 0
        self._tick_time_data = dict()
        self._num_frames = 0
        self._last_frame_time = 0.0
        self._start_time = 0.0
        self._stop_time = 0.0
        self._strand_keys = list()
        self._enable_profiling = enable_profiling
        self._constant_preset = ""
        self._paused = False
        self._frozen = False
        self._preset_changed_callback = None

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
            self._output_buffer = np.zeros((maxs, maxf, maxp, 3))
            self._output_back_buffer = np.zeros((maxs, maxf, maxp, 3))
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

    def on_tick_timer(self):
        if self._frozen:
            delay = 1.0 / self._tick_rate
        else:
            start = time.clock()
            self.tick()
            dt = (time.clock() - start)
            delay = max(0, (1.0 / self._tick_rate) - dt)
            self._elapsed += (1.0 / self._tick_rate)
        if self._running:
            self._tick_timer = threading.Timer(delay, self.on_tick_timer)
            self._tick_timer.start()

    def set_constant_preset(self, preset_name):
        self._constant_preset = preset_name
        for idx, preset in enumerate(self._presets):
            if preset.__class__.__name__ == preset_name:
                self._active_preset = idx

        if self._preset_changed_callback is not None:
            self._preset_changed_callback(self.get_active_preset())

        self._presets[self._active_preset].reset()
        self._paused = True

    def add_preset(self, preset):
        """
        Appends a preset to the end of the current playlist
        """
        self._presets.append(preset(self))

    def get_preset_playlist(self):
        """
        Returns the current playlist, in order.
        """
        return self._presets

    def reorder_preset_playlist(self, order):
        """
        Defines a new order for the current playlist.
        """
        assert(len(order) == len(self._presets))
        self._presets = [[self._presets[i] for i in order]]

    def clear_preset_playlist(self):
        """
        Wipes the current playlist.  Does not change the playback state.
        """
        self._presets = []

    def get_tick_rate(self):
        return self._tick_rate

    def get_active_preset(self):
        """
        Returns the active preset (the object itself!)
        """
        return self._presets[self._active_preset]

    def get_active_preset_name(self):
        """
        Returns (for display purposes) the name of the active preset
        """
        return self._presets[self._active_preset].__class__.__name__

    def set_active_preset_by_name(self, preset_name):
        for i, preset in enumerate(self._presets):
            if preset.__class__.__name__ == preset_name:
                self.start_transition(i)

    def next(self):
        self.start_transition((self._active_preset + 1) % len(self._presets))

    def prev(self):
        self.start_transition((self._active_preset - 1) % len(self._presets))

    def start_transition(self, next=None):
        if next is not None:
            self._next_preset = next
        self._in_transition = True


    def tick(self):
        self._num_frames += 1
        if len(self._presets) > 0:
            self._presets[self._active_preset].clear_commands()
            self._presets[self._active_preset].tick()
            transition_progress = 0.0

            # Handle transition by rendering both the active and the next preset, and blending them together
            if self._in_transition:
                if self._elapsed == 0.0:
                    self._presets[self._next_preset].reset()
                if self._transition_duration > 0.0:
                    transition_progress = self._elapsed / self._transition_duration
                else:
                    transition_progress = 1.0
                self._presets[self._next_preset].clear_commands()
                self._presets[self._next_preset].tick()

                # Exit from transition state after the transition duration has elapsed
                if transition_progress >= 1.0:
                    self._in_transition = False
                    # Reset the elapsed time counter so the preset runs for the full duration after the transition
                    self._elapsed = 0.0
                    self._active_preset = self._next_preset
                    self._next_preset = (self._next_preset + 1) % len(self._presets)
                    if self._preset_changed_callback is not None:
                        self._preset_changed_callback(self.get_active_preset())

            # If the scene tree is available, we can do efficient mixing of presets.
            # If not, a tree would need to be constructed on-the-fly.
            # TODO: Support mixing without a scene tree available
            if self._enable_rendering:
                if self._in_transition:
                    self.render_presets(self._active_preset, self._next_preset, transition_progress)
                else:
                    self.render_presets(self._active_preset)
            else:
                if self._net is not None:
                    self._net.write(self._presets[self._active_preset].get_commands_packed())

            if not self._paused and (self._elapsed >= self._duration) and self._presets[self._active_preset].can_transition():
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

    def render_presets(self, first, second=None, blend_state=0.0):
        """
        Grabs the command output from a preset with the index given by first.
        If a second preset index is given, render_preset will blend the two together
        according to blend_state (0.0 = 100% first, 1.0 = 100% second)
        """
        if first >= len(self._presets):
            raise ValueError("first index %d out of range" % first)
        if second is not None:
            if second >= len(self._presets):
                raise ValueError("second index %d out of range" % second)
            if blend_state < 0.0 or blend_state > 1.0:
                raise ValueError("blend_state %f out of range: must be between 0.0 and 1.0" % blend_state)

        #self.reset_output_buffer()
        if self._enable_profiling:
            start = time.time()

        commands = []

        if isinstance(self._presets[first], RawPreset):
            self._output_buffer = self._presets[first].get_buffer()
        else:
            commands = self._presets[first].get_commands()
            #print commands
            self.render_command_list(commands, self._output_buffer)

        if self._enable_profiling:
            dt = 1000.0 * (time.time() - start)
            if dt > 10.0:
                log.info("rendered first preset in %0.2f ms (%d commands)" % (dt, len(commands)))

        if second is not None:
            if self._enable_profiling:
                start = time.time()

            second_commands = self._presets[second].get_commands()
            self.render_command_list(second_commands, self._output_back_buffer)

            if self._enable_profiling:
                dt = 1000.0 * (time.time() - start)
                if dt > 10.0:
                    log.info("rendered second preset in %0.2f ms (%d commands)" % (dt, len(second_commands)))

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
        data = self._output_buffer[strand_key].astype(int).tolist()
        data_flat = [item for sublist in data for item in sublist]
        data_flat = [item for sublist in data_flat for item in sublist]
        return data_flat[0:3 * len_strand]

    def reset_output_buffer(self):
        """
        Clears the output buffer
        """
        self._output_buffer = np.zeros((len(self._strand_keys), self._max_fixtures, self._max_pixels, 3))
        self._output_back_buffer = np.zeros((len(self._strand_keys), self._max_fixtures, self._max_pixels, 3))

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

    def blend(self, color1, color2, blend_state):
        """
        Returns a 3-tuple (R, G, B) of the equal-weighted blend between the two input colors.
        """
        if blend_state == 0.0:
            return color1
        elif blend_state == 1.0:
            return color2
        else:
            # TODO: This blending operation desaturates the output during transition.  Switch to HSV blending on Hue
            inv_state = 1.0 - blend_state
            return (int((color1[0] * inv_state) + (color2[0] * blend_state)),
                    int((color1[1] * inv_state) + (color2[1] * blend_state)),
                    int((color1[2] * inv_state) + (color2[2] * blend_state)))

    def set_preset_changed_callback(self, cb):
        self._preset_changed_callback = cb
