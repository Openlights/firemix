from presets.rgb_fade import RGBFade
from presets.separate_strand_rgb import SeparateStrandRGB
from presets.separate_strand_with_flash import SeparateStrandWithFlash

class Mixer:

    def __init__(self, net=None, tick_rate=30.0):
        self.presets = []
        self.net = net
        self.tick_rate = tick_rate

        self.demo_preset()

    def demo_preset(self):
        self.presets.append(SeparateStrandWithFlash(self))

    def tick(self):
        self.presets[0].clr_cmd()
        self.presets[0].tick()
        if self.net is not None:
            self.net.write(self.presets[0].get_cmd())
