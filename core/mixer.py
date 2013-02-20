from presets.rgb_fade import RGBFade


class Mixer:

    def __init__(self, net=None, tick_rate=60.0):
        self.presets = []
        self.net = net
        self.tick_rate = tick_rate

        self.demo_preset()

    def demo_preset(self):
        self.presets.append(RGBFade(self))

    def tick(self):
        self.presets[0].tick()
        if self.net is not None:
            self.net.write(self.presets[0].get_cmd())
