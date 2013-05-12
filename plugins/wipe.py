import numpy as np

from lib.transition import Transition
from lib.buffer_utils import BufferUtils


class Wipe(Transition):
    """
    Implements a simple wipe
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Wipe"

    def setup(self):
        self.num_strands, self.num_pixels = BufferUtils.get_buffer_size(self._app)
        self.mask = np.tile(False, (self.num_strands, self.num_pixels, 3))

        fl = [f.midpoint()[0] for f in self._app.scene.fixtures()]
        self.min_x = min(fl)
        max_x = max(fl)
        self.span_x = max_x - self.min_x

        self.locations = []
        for f in self._app.scene.fixtures():
            for p in range(f.pixels):
                self.locations.append((f.strand, f.address, p, self._app.scene.get_pixel_location((f.strand, f.address, p))))

    def get(self, start, end, progress):
        """
        Simple wipe
        """

        for strand, address, pixel, location in self.locations:
            #print strand, address, midpoint[0], (self.min_x + (progress * self.span_x))
            if location[0] < (self.min_x + (progress * self.span_x)):
                _, pixel = BufferUtils.get_buffer_address(self._app, (strand, address, pixel))
                self.mask[strand][pixel][:] = True

        #print progress, self.mask

        start[self.mask] = 0.0
        end[np.invert(self.mask)] = 0.0
        return start + end