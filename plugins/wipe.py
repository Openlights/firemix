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

    def reset(self):
        self.buffer_size = BufferUtils.get_buffer_size()

        bb = self._app.scene.get_fixture_bounding_box()
        self.scene_center = np.asarray([bb[0] + (bb[2] - bb[0]) / 2, bb[1] + (bb[3] - bb[1]) / 2])
        self.bb = bb
        self.mask = np.tile(False, (self.buffer_size, 3))
        angle = np.random.random() * np.pi * 2.0
        self.wipe_vector = np.zeros((2))

        self.wipe_vector[0] = math.cos(angle)
        self.wipe_vector[1] = math.sin(angle)

        self.locations = self._app.scene.get_all_pixel_locations()

        # Determine the endpoints of the wipe line
        self.wipe_start = np.copy(self.scene_center)
        wipe_end = np.copy(self.scene_center)
        neg_d = 999999
        pos_d = -999999
        for location in self.locations:
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
        for offset, location in enumerate(self.locations):
            if np.dot(location - wipe_point, self.wipe_vector) < 0:
                self.mask[offset][:] = True

        start[self.mask] = 0.0
        end[np.invert(self.mask)] = 0.0
        return start + end
