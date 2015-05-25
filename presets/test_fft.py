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

from lib.raw_preset import RawPreset
from lib.color_fade import ColorFade

class TestFFT(RawPreset):
    """Simple test for FFT data coming from aubio"""

    _fader = None
    _fader_steps = 256
    
    def setup(self):
        self.parameter_changed(None)
        self._fader = ColorFade([(0.0, 0.5, 1.0), (1.0, 0.5, 1.0), (0.0, 0.5, 1.0)], self._fader_steps)
        self._fft_normalized = [1.0, 0.75, 0.5, 0.35, 0.2, 0.1]

    def parameter_changed(self, parameter):
        pass

    def reset(self):
        self.locations = self.scene().get_all_pixel_locations()

    def draw(self, dt):

        def rotate(l, n):
            return l[n:] + l[:n]

        if self._mixer.is_onset():
            self._fft_normalized = rotate(self._fft_normalized, 1)

        angle_bin_width = (2.0 * math.pi) / len(self._fft_normalized)

        cx, cy = self.scene().center_point()
        x,y = (self.locations - (cx, cy)).T
        self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
        self.pixel_angles = np.arctan2(y, x) + math.pi
        self.pixel_distances /= max(self.pixel_distances)

        for bin in range(len(self._fft_normalized)):
            start = bin * angle_bin_width
            end = (bin + 1) * angle_bin_width
            mask = (self.pixel_angles > start) & (self.pixel_angles < end)
            self.pixel_distances[mask] *= self._fft_normalized[bin]

        angles = self.pixel_angles / (4.0 * math.pi)
        hues = np.abs(angles - 0.5)
        lights = 0.5 * (1.0 - self.pixel_distances)
        hues = np.int_(np.mod(hues, 1.0) * self._fader_steps)
        colors = self._fader.color_cache[hues]
        colors = colors.T
        colors[0] = np.mod(colors[0], 1.0)
        colors[1] = lights
        colors = colors.T

        self._pixel_buffer = colors