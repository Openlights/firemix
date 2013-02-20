import colorsys

from lib.preset import Preset


class RGBFade(Preset):
    """Simple RGB fade"""

    h = 0.0

    def setup(self):
        pass

    def tick(self):
        rgb_color = [int(255.0 * c) for c in colorsys.hsv_to_rgb(self.h, 1.0, 1.0)]
        self.set_all(rgb_color)
        self.h += 0.001 * self.tick_rate()
        if self.h > 1.0:
            self.h = 0.0
