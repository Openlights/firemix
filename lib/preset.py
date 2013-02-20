


class Preset:
    """Base Preset.  Does nothing."""

    def __init__(self, mixer):
        self._mixer = mixer
        self._cmd = []

    def setup(self):
        """Override this method to run any init code your preset needs."""
        pass

    def tick(self):
        """Override this method to draw the output of your preset.  It will be called each tick."""
        pass

    def tick_rate(self):
        return self._mixer.tick_rate

    def get_cmd(self):
        return self._cmd

    def set_all(self, color):
        self._mixer.net.write([-1, -1, -1, color[0], color[1], color[2]])

    def set_strand(self, strand, color):
        self._mixer.net.write([strand, -1, -1, color[0], color[1], color[2]])

    def set_fixture(self, strand, address, color):
        self._mixer.net.write([strand, address, -1, color[0], color[1], color[2]])

    def set(self, strand, address, pixel, color):
        self._mixer.net.write([strand, address, pixel, color[0], color[1], color[2]])
