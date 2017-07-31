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
        locations = self._app.scene.get_all_pixel_locations()
        locations -= self._app.scene.center_point()
        #locations -= locations[np.random.randint(0, len(locations) - 1)]
        locations = np.square(locations)
        self.distances = locations.T[0] + locations.T[1]
        self.distances /= max(self.distances)

    def get(self, start, end, progress):
        buffer = np.where(self.distances < progress, end, start)
        buffer['light'][np.abs(self.distances - progress) < 0.02] += 0.5 # we can apply effects to transition line here

        return buffer
