import numpy as np
from math import fabs
from noise import snoise3

from lib.transition import Transition
from lib.buffer_utils import BufferUtils


class SimplexBlend(Transition):
    """
    Blends using a simplex noise mask
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Simplex Blend"

    def reset(self):
        buffer_size = BufferUtils.get_buffer_size()
        self.frame = np.tile(0.0, (buffer_size, 3))
        self.pixel_locations = self._app.scene.get_all_pixel_locations()

    def get(self, start, end, progress):
        for pixel, loc in enumerate(self.pixel_locations):
            blend = (1.0 + snoise3(0.01 * loc[0], 0.01 * loc[1], progress, 1, 0.5, 0.5)) / 2.0
            self.frame[pixel] = blend * start[pixel] + ((1.0 - blend) * end[pixel])

        # Mix = 1.0 when progress = 0.5, 0.0 at either extreme
        mix = 1.0 - fabs(2.0 * (progress - 0.5))

        if progress < 0.5:
            return ((1.0 - mix) * start) + (mix * self.frame)
        else:
            return (mix * self.frame) + ((1.0 - mix) * end)