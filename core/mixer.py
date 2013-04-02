from presets.rgb_fade import RGBFade
from presets.separate_strand_rgb import SeparateStrandRGB
from presets.fixture_step_fade import FixtureStepFade

class Mixer:

    def __init__(self, net=None, tick_rate=30.0):
        self._presets = []
        self.net = net
        self.tick_rate = tick_rate

        self.demo_preset()

    def demo_preset(self):
        self.presets.append(FixtureStepFade(self))

    def add_preset(self, preset):
        """
        appends a preset to the end of the current playlist
        """
        self._presets.append(preset(self))

    def get_preset_playlist(self):
        """
        returns the current playlist, in order.
        """
        return self._presets

    def reorder_preset_playlist(self, order):
        """
        defines a new order for the current playlist.
        """
        assert(len(order) == len(self._presets))
        self._presets = [[self._presets[i] for i in order]]

    def tick(self):
        self.presets[0].clr_cmd()
        self.presets[0].tick()
        if self.net is not None:
            self.net.write(self.presets[0].get_cmd())
