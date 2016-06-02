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

from lib.pattern import Pattern
from lib.buffer_utils import BufferUtils
from lib.parameters import HLSParameter

# Defaults
DEFAULT_COLOR = (0.0, 0.5, 1.0)


class SolidColor(Pattern):
    """Solid color"""

    # Configurable parameters
    _color = DEFAULT_COLOR

    # Internal parameters
    def setup(self):
        self.add_parameter(HLSParameter('color', self._color))
        self._pixels = self.scene().get_all_pixels()
        super(SolidColor, self).setup()

    def parameter_changed(self, parameter):
        self._color = self.parameter('color').get()

    def reset(self):
        self._color = DEFAULT_COLOR
        self.parameter_changed(None)

    def draw(self, dt):
        self.setAllHLS(self._color[0], self._color[1], self._color[2])

