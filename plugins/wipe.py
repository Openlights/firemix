# This file is part of Firemix.
#
# Copyright 2013-2015 Jonathan Evans <jon@craftyjon.com>
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

class Wipe(Transition):
    """
    Implements a simple wipe
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Wipe"

    def reset(self):
        angle = np.random.random() * np.pi * 2.0
        self.wipe_vector = np.zeros((2))

        self.wipe_vector[0] = math.cos(angle)
        self.wipe_vector[1] = math.sin(angle)

        self.locations = self._app.scene.get_all_pixel_locations()

        self.dots = np.dot(self.locations, self.wipe_vector)
        maxDot = max(self.dots)
        minDot = min(self.dots)
        self.dots -= minDot
        self.dots /= maxDot - minDot

    def get(self, start, end, progress):
        buffer = np.where(self.dots < progress, end.T, start.T)
        buffer[1][np.abs(self.dots - progress) < 0.02] += 0.5 # we can apply effects to transition line here
        buffer = buffer.T

        return buffer
