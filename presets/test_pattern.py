import numpy as np

from lib.raw_preset import RawPreset

class TestPattern(RawPreset):
    """Simple RGB test pattern"""

    def setup(self):
        self._pixels = self.scene().get_all_pixels()

    def reset(self):
        pass

    def draw(self, dt):
        hues = np.asarray([0.0, 0.33, 0.66] * (len(self._pixels) + 1 / 3))[0:len(self._pixels)]
        luminances = np.asarray([0.5] * len(self._pixels))
        self.setAllHLS(hues, luminances, 1.0)