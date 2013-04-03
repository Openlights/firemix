import threading
import logging

log = logging.getLogger("FireMix.Mixer")


class Mixer:
    """
    Mixer is the brains of FireMix.  It handles the playback of presets
    and the generation of the final command stream to send to the output
    device(s).
    """

    def __init__(self, net=None, tick_rate=30.0, preset_duration=5.0):
        self._presets = []
        self._net = net
        self._tick_rate = tick_rate
        self._active_preset = 0
        self._tick_timer = None
        self._duration = preset_duration
        self._elapsed = 0.0
        self._running = False

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

    def advance(self, dir=1):
        """
        Transitions to the next preset in the playlist (or previous, if dir == -1)
        """
        self._active_preset = (self._active_preset + dir) % len(self._presets)
        log.info("Advanced to %s" % self.get_active_preset_name())

    def tick(self):
        if len(self._presets) > 0:
            self._presets[self._active_preset].clr_cmd()
            self._presets[self._active_preset].tick()
            if self._net is not None:
                self._net.write(self._presets[self._active_preset].get_cmd())

            if (self._elapsed >= self._duration) and self._presets[self._active_preset].can_transition():
                self.advance()
                self._elapsed = 0.0
