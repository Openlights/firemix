import numpy as np
import math

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

        bb = self._app.scene.get_fixture_bounding_box()
        self.scene_center = np.asarray([bb[0] + (bb[2] - bb[0]) / 2, bb[1] + (bb[3] - bb[1]) / 2])
        self.bb = bb

        self.reset()

    def reset(self):
        self.mask = np.tile(False, (self.num_strands, self.num_pixels, 3))
        angle = np.random.random() * np.pi * 2.0
        self.wipe_vector = np.zeros((2))

        self.wipe_vector[0] = math.cos(angle)
        self.wipe_vector[1] = math.sin(angle)

        self.locations = []
        for f in self._app.scene.fixtures():
            for p in range(f.pixels):
                self.locations.append((f.strand, f.address, p, np.asarray(self._app.scene.get_pixel_location((f.strand, f.address, p)))))

        # Determine the endpoints of the wipe line
        self.wipe_start = np.copy(self.scene_center)
        wipe_end = np.copy(self.scene_center)
        neg_d = 999999
        pos_d = -999999
        for s, a, p, location in self.locations:
            # Project vector from the center to the pixel with the wipe vector
            pixel_vector = location - self.scene_center
            dp = np.dot(pixel_vector, self.wipe_vector)
            if dp > pos_d:
                pos_d = dp
                wipe_end = location
            elif dp < neg_d:
                neg_d = dp
                self.wipe_start = location

        self.wipe_line_vector = np.asarray([wipe_end[0] - self.wipe_start[0], wipe_end[1] - self.wipe_start[1]])

    def get(self, start, end, progress):
        """
        Simple wipe
        """
        # Move the wipe point along the wipe line
        wipe_point = self.wipe_start + (progress * self.wipe_line_vector)

        # Mask based on the wipe point
        for strand, address, pixel, location in self.locations:
            if np.dot(location - wipe_point, self.wipe_vector) < 0:
                _, pixel = BufferUtils.get_buffer_address(self._app, (strand, address, pixel))
                self.mask[strand][pixel][:] = True

        start[self.mask] = 0.0
        end[np.invert(self.mask)] = 0.0
        return start + end
