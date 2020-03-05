# This file is part of Firemix.
#
# Copyright 2013-2020 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Firemix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Firemix.  If not, see <http://www.gnu.org/licenses/>.

from builtins import range
import numpy as np
from math import fmod, fabs, sqrt, pow, tan, pi, atan2
from copy import deepcopy

from lib.transition import Transition
from lib.buffer_utils import BufferUtils, struct_flat


class Spiral(Transition):
    """
    Spiral wipe
    """

    def __init__(self, app):
        Transition.__init__(self, app)
        self.revolutions = 3
        self.angle = 0.0
        self.radius = 0.0

    def __str__(self):
        return "Spiral"

    def reset(self):
        self.buffer_size = BufferUtils.get_buffer_size()

        self.scene_bb = self._app.scene.get_fixture_bounding_box()
        self.scene_center = (self.scene_bb[0] + (self.scene_bb[2] - self.scene_bb[0]) / 2,
                             self.scene_bb[1] + (self.scene_bb[3] - self.scene_bb[1]) / 2)
        dx = self.scene_bb[2] - self.scene_center[0]
        dy = self.scene_bb[3] - self.scene_center[1]

        self.locations = self._app.scene.get_all_pixel_locations()
        self.angles = {}
        self.radii = {}
        for pixel, location in enumerate(self.locations):
            dy = location[1] - self.scene_center[1]
            dx = location[0] - self.scene_center[0]
            angle = (atan2(dy, dx) + pi) / (2.0 * pi)
            self.radii[pixel] = sqrt(pow(dx,2) + pow(dy, 2))
            self.angles[pixel] = angle

        self.scene_radius = max(self.radii)

        self.mask = np.tile(False, self.buffer_size)
        self.angle = 0.0
        self.radius = 0.0
        self.active = [True,] * len(self.locations)

    def render(self, start, end, progress, out):

        radius_progress = fmod(progress * self.revolutions, 1.0)
        distance_progress = self.scene_radius * progress
        distance_cutoff = (1.0 / self.revolutions) * self.scene_radius * progress

        for pixel in range(len(self.active)):
            #if not self.active[pixel]:
            #    continue
            angle = self.angles[pixel]
            distance = self.radii[pixel]

            if distance < distance_cutoff or (distance < distance_progress and angle < radius_progress):
                self.mask[pixel] = True
                #self.active[pixel] = False
            else:
                self.mask[pixel] = False

        start[self.mask] = (0.0, 0.0, 0.0)
        end[np.invert(self.mask)] = (0.0, 0.0, 0.0)
        np.add(struct_flat(start), struct_flat(end), struct_flat(out))

    def _is_point_inside_wipe(self, point, progress):
        return np.dot((point - self.wipe_point), self.wipe_vector) >= 0
