# This file is part of Firemix.
#
# Copyright 2013-2016 Jonathan Evans <jon@craftyjon.com>
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

import numpy as np
from math import fabs
from vec_noise import snoise3

from lib.transition import Transition
from lib.buffer_utils import BufferUtils, struct_flat


class SimplexBlend(Transition):
    """
    Blends using a simplex noise mask
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Simplex Blend"

    def reset(self):
        self.frame = BufferUtils.create_buffer()
        pixel_locations = np.asarray(self._app.scene.get_all_pixel_locations()).T
        self.scaled_pixel_xs = 0.01 * pixel_locations[0]
        self.scaled_pixel_ys = 0.01 * pixel_locations[1]

    def get(self, start, end, progress):
        blend = snoise3(self.scaled_pixel_xs, self.scaled_pixel_ys,
                        progress, 1, 0.5, 0.5)
        # Apply the blend to all three color components
        for comp in ('hue', 'light', 'sat'):
            self.frame[comp] = blend * start[comp] + ((1.0 - blend) * end[comp])

        # Mix = 1.0 when progress = 0.5, 0.0 at either extreme
        mix = 1.0 - fabs(2.0 * (progress - 0.5))

        flat_frame = struct_flat(self.frame)
        if progress < 0.5:
            flat_frame = ((1.0 - mix) * struct_flat(start)) + (mix * flat_frame)
        else:
            flat_frame = (mix * flat_frame) + ((1.0 - mix) * struct_flat(end))

        return self.frame
