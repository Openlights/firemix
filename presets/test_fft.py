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
from lib.parameters import FloatParameter
from lib.color_fade import ColorFade

class TestFFT(RawPreset):
    """Simple test for FFT data coming from aubio"""

    _fader = None
    _fader_steps = 256
    _onset_decay = 0.0
    
    def setup(self):
        self.parameter_changed(None)
        self._fader = ColorFade([(0.0, 0.5, 1.0), (1.0, 0.5, 1.0), (0.0, 0.5, 1.0)], self._fader_steps)
        self._fft_normalized = [0.0] * 8
        self.add_parameter(FloatParameter('fft-weight', 25.0))

    def parameter_changed(self, parameter):
        pass

    def reset(self):
        self.locations = self.scene().get_all_pixel_locations()

    def draw(self, dt):

        def rotate(l, n):
            return l[n:] + l[:n]

        self.fft = self._mixer.fft_data()
        #self._fft_normalized = [i if i == 0 else (i / max(self._fft_normalized)) for i in self._fft_normalized]

        angle_bin_width = (2.0 * math.pi) / len(self.fft)

        if self._mixer.is_onset():
            self._onset_decay = 1.0
        elif self._onset_decay > 0.0:
            self._onset_decay -= 0.05


        cx, cy = self.scene().center_point()
        x,y = (self.locations - (cx, cy)).T
        self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
        self.pixel_angles = np.arctan2(y, x) + math.pi
        self.pixel_distances /= max(self.pixel_distances)
        self.pixel_amplitudes = self.pixel_distances

        for bin in range(len(self.fft)):
            start = bin * angle_bin_width
            end = (bin + 1) * angle_bin_width
            mask = (self.pixel_angles > start) & (self.pixel_angles < end)
            self.pixel_amplitudes[mask] = (self.parameter('fft-weight').get() * self.fft[bin])

        angles = self.pixel_angles / (4.0 * math.pi)
        hues = np.abs(angles - 0.5)
        lights = (0.5 * (1.0 - self.pixel_distances) * self.pixel_amplitudes) + (0.5 * self._onset_decay)
        hues = np.int_(np.mod(hues, 1.0) * self._fader_steps)
        colors = self._fader.color_cache[hues]
        colors = colors.T
        colors[0] = np.mod(colors[0], 1.0)
        colors[1] = lights
        colors = colors.T

        self._pixel_buffer = colors