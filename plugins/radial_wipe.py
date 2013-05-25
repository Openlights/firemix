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

    def setup(self):
        self.num_strands, self.num_pixels = BufferUtils.get_buffer_size(self._app)

        self.scene_bb = self._app.scene.get_fixture_bounding_box()
        self.scene_center = (self.scene_bb[0] + (self.scene_bb[2] - self.scene_bb[0]) / 2, self.scene_bb[1] + (self.scene_bb[3] - self.scene_bb[1]) / 2)
        dx = self.scene_bb[2] - self.scene_center[0]
        dy = self.scene_bb[3] - self.scene_center[1]
        self.radius = math.sqrt(math.pow(dx,2) + math.pow(dy, 2))

    def reset(self):
        self.mask = np.tile(False, (self.num_strands, self.num_pixels, 3))

        self.locations = []
        for f in self._app.scene.fixtures():
            for p in range(f.pixels):
                self.locations.append((f.strand, f.address, p, self._app.scene.get_pixel_location((f.strand, f.address, p))))

    def get(self, start, end, progress):

        for strand, address, pixel, location in self.locations:
            dy = math.fabs(location[1] - self.scene_center[1])
            dx = math.fabs(location[0] - self.scene_center[0])
            if math.sqrt(math.pow(dx,2) + math.pow(dy, 2)) < (self.radius * progress):
                _, pixel = BufferUtils.get_buffer_address(self._app, (strand, address, pixel))
                self.mask[strand][pixel][:] = True

        start[self.mask] = 0.0
        end[np.invert(self.mask)] = 0.0
        return start + end

    def _is_point_inside_wipe(self, point, progress):
        return np.dot((point - self.wipe_point), self.wipe_vector) >= 0