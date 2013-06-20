import numpy as np
import math

from lib.transition import Transition
from lib.buffer_utils import BufferUtils


class RadialWipe(Transition):
    """
    Implements a radial wipe (Iris) transition
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Radial Wipe"

    def reset(self):
        self.buffer_size = BufferUtils.get_buffer_size()

        self.scene_bb = self._app.scene.get_fixture_bounding_box()
        self.scene_center = (self.scene_bb[0] + (self.scene_bb[2] - self.scene_bb[0]) / 2, self.scene_bb[1] + (self.scene_bb[3] - self.scene_bb[1]) / 2)
        dx = self.scene_bb[2] - self.scene_center[0]
        dy = self.scene_bb[3] - self.scene_center[1]
        self.radius = math.sqrt(math.pow(dx,2) + math.pow(dy, 2))

        self.mask = np.tile(False, (self.buffer_size, 3))
        self.locations = self._app.scene.get_all_pixel_locations()

    def get(self, start, end, progress):

        for pixel, location in enumerate(self.locations):
            dy = math.fabs(location[1] - self.scene_center[1])
            dx = math.fabs(location[0] - self.scene_center[0])
            if math.sqrt(math.pow(dx,2) + math.pow(dy, 2)) < (self.radius * progress):
                self.mask[pixel][:] = True

        start[self.mask] = 0.0
        end[np.invert(self.mask)] = 0.0
        return start + end

    def _is_point_inside_wipe(self, point, progress):
        return np.dot((point - self.wipe_point), self.wipe_vector) >= 0