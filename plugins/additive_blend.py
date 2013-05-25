import numpy as np
from math import fabs

from lib.transition import Transition
from lib.buffer_utils import BufferUtils


class AdditiveBlend(Transition):
    """
    Blends using some kind of additive color mixing
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Additive Blend"

    def setup(self):
        x, y = BufferUtils.get_buffer_size(self._app)
        self.frame = np.tile(np.array([0.0], dtype=np.uint8), (x, y, 3))

        self.pixel_locations = self._app.scene.get_all_pixel_locations()
        self.pixel_addr = {}
        for pixel, _ in self.pixel_locations:
            self.pixel_addr[pixel] = BufferUtils.get_buffer_address(self._app, pixel)

    def get(self, start, end, progress):

        if progress >= 0.75:
            start = 4.0 * (1.0 - progress) * start
        if progress <= 0.25:
            end = (4.0 * progress) * end

        self.frame = start.astype(np.uint8) + end.astype(np.uint8)

        # for pixel, loc in self.pixel_locations:
        #     a, b = self.pixel_addr[pixel]
        #     s = start.astype(np.uint16)[a][b] + end.astype(np.uint16)[a][b]
        #     m = max(s)
        #     if m > 255:
        #         r = 255.0 / m
        #         s = s * r
        #     #print s
        #     self.frame[a][b] = s

        return self.frame