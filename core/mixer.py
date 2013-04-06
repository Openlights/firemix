import threading
import logging

from lib.commands import SetAll, SetStrand, SetFixture, SetPixel

log = logging.getLogger("FireMix.Mixer")


class Mixer:
    """
    Mixer is the brains of FireMix.  It handles the playback of presets
    and the generation of the final command stream to send to the output
    device(s).
    """

    def __init__(self, net=None, scene=None, tick_rate=30.0, preset_duration=5.0):
        self._presets = []
        self._net = net
        self._scene = scene
        self._tick_rate = tick_rate
        self._active_preset = 0
        self._next_preset = 1
        self._in_transition = False
        self._transition_duration = 2.0
        self._tick_timer = None
        self._duration = preset_duration
        self._elapsed = 0.0
        self._running = False
        self._enable_rendering = True
        self._output_buffer = None

        if not self._scene:
            log.warn("No scene assigned to mixer.  Preset rendering and transitions are disabled.")
            self._transition_duration = 0.0
            self._enable_rendering = False
        else:
            log.info("Initializing preset rendering buffer")
            fh = self._scene.fixture_hierarchy()
            self._output_buffer = dict()
            for strand in fh:
                self._output_buffer[strand] = dict()
                for address in fh[strand]:
                    self._output_buffer[strand][address] = [(0, 0, 0)] * fh[strand][address].pixels()

    def run(self):
        if not self._running:
            self._tick_timer = threading.Timer(1.0 / self._tick_rate, self.on_tick_timer)
            self._tick_timer.start()
            self._running = True
            self._elapsed = 0.0

    def stop(self):
        self._running = False

    def on_tick_timer(self):
        self.tick()
        self._elapsed += (1.0 / self._tick_rate)
        if self._running:
            self._tick_timer = threading.Timer(1.0 / self._tick_rate, self.on_tick_timer)
            self._tick_timer.start()

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

    def start_transition(self, next=None):
        if next is not None:
            self._next_preset = next
        self._in_transition = True


    def tick(self):
        if len(self._presets) > 0:
            self._presets[self._active_preset].clear_commands()
            self._presets[self._active_preset].tick()
            transition_progress = 0.0

            # Handle transition by rendering both the active and the next preset, and blending them together
            if self._in_transition:
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

            if (self._elapsed >= self._duration) and self._presets[self._active_preset].can_transition():
                self.start_transition()
                self._elapsed = 0.0

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

        commands = self._presets[first].get_commands()

        if second is not None:
            pass

        if self._net is not None:
            self._net.write([cmd.pack() for cmd in commands])

    def additive_blend(self, cmd1, cmd2):
        pass
