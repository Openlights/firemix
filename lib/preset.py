


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

    def clr_cmd(self):
        self._cmd = []

    def get_cmd(self):
        return self._cmd

    def set_all(self, color):
        self._cmd.append([0x21, 0x00, 0x03, color[0], color[1], color[2]])
        #self._mixer.net.write([-1, -1, -1, color[0], color[1], color[2]])

    def set_strand(self, strand, color):
        self._cmd.append([0x22, 0x00, 0x04, strand, color[0], color[1], color[2]])
        #self._mixer.net.write([strand, -1, -1, color[0], color[1], color[2]])

    def set_fixture(self, strand, address, color):
        self._cmd.append([0x23, 0x00, 0x05, strand, address, color[0], color[1], color[2]])
        #self._mixer.net.write([strand, address, -1, color[0], color[1], color[2]])

    def set(self, strand, address, pixel, color):
        self._cmd.append([0x24, 0x00, 0x06, strand, address, pixel, color[0], color[1], color[2]])
        #self._mixer.net.write([strand, address, pixel, color[0], color[1], color[2]])
