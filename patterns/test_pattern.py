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

class TestPattern(Pattern):
    """Array calibration pattern"""

    def setup(self):
        self._pixels = self.scene().get_all_pixels()
        self._hierarchy = self.scene().fixture_hierarchy()
        self._hue = 0.0
        super(TestPattern, self).setup()

    def reset(self):
        pass

    def draw(self, dt):
        self._hue = (self._hue + (dt * 0.1)) % 1.0
        self.setAllHLS(self._hue, 0.2, 1.0)
        for strand in self._hierarchy:
            self.setPixelHLS(BufferUtils.logical_to_index((strand, 0, 0), scene=self.scene()), (0.33, 0.5, 1.0))

            if (strand & 0x8):
                self.setPixelHLS(BufferUtils.logical_to_index((strand, 0, 1), scene=self.scene()), (0.66, 0.9, 1.0))
            else:
                self.setPixelHLS(BufferUtils.logical_to_index((strand, 0, 1), scene=self.scene()), (0.0, 0.2, 0.0))
            if (strand & 0x4):
                self.setPixelHLS(BufferUtils.logical_to_index((strand, 0, 2), scene=self.scene()), (0.66, 0.9, 1.0))
            else:
                self.setPixelHLS(BufferUtils.logical_to_index((strand, 0, 2), scene=self.scene()), (0.0, 0.2, 0.0))
            if (strand & 0x2):
                self.setPixelHLS(BufferUtils.logical_to_index((strand, 0, 3), scene=self.scene()), (0.66, 0.9, 1.0))
            else:
                self.setPixelHLS(BufferUtils.logical_to_index((strand, 0, 3), scene=self.scene()), (0.0, 0.2, 0.0))
            if (strand & 0x1):
                self.setPixelHLS(BufferUtils.logical_to_index((strand, 0, 4), scene=self.scene()), (0.66, 0.9, 1.0))
            else:
                self.setPixelHLS(BufferUtils.logical_to_index((strand, 0, 4), scene=self.scene()), (0.0, 0.2, 0.0))

            for fixture in self._hierarchy[strand]:
                last_fixture_pixel = self._hierarchy[strand][fixture].pixels - 1
                self.setPixelHLS(BufferUtils.logical_to_index((strand, fixture, last_fixture_pixel), scene=self.scene()), (0.66, 0.5, 1.0))
                if fixture > 0:
                    self.setPixelHLS(BufferUtils.logical_to_index((strand, fixture, 0), scene=self.scene()), (0.15, 0.5, 1.0))

            last_fixture = len(self._hierarchy[strand].keys()) - 1
            last_pixel = self._hierarchy[strand][last_fixture].pixels - 1

            self.setPixelHLS(BufferUtils.logical_to_index((strand, last_fixture, last_pixel), scene=self.scene()), (0.0, 0.5, 1.0))
