# This file is part of Firemix.
#
# Copyright 2013-2015 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

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