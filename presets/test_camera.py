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

from lib.raw_preset import RawPreset
from lib.buffer_utils import BufferUtils

class TestCamera(RawPreset):
    """Display the camera data on all pixels"""

    def setup(self):
        pass

    def reset(self):
        pass

    def draw(self, dt):
        ir_values = self.scene().get_all_pixels_image_mapped(self._mixer._camera_data)
        self.setAllHLS(0.0, ir_values, 0.0)
