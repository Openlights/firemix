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
        self.x, self.y = BufferUtils.get_buffer_size(self._app)

        self.pixel_locations = self._app.scene.get_all_pixel_locations()
        self.pixel_addr = {}
        for pixel, _ in self.pixel_locations:
            self.pixel_addr[pixel] = BufferUtils.get_buffer_address(self._app, pixel)

        self.reset()

    def reset(self):
        self.frame = np.tile(np.array([0.0], dtype=np.uint8), (self.x, self.y, 3))

    def get(self, start, end, progress):

        if progress >= 0.5:
            start = 2.0 * (1.0 - progress) * start
        if progress <= 0.25:
            end = (4.0 * progress) * end
        
        (start + end).clip(0, 255, out=self.frame)

        return self.frame