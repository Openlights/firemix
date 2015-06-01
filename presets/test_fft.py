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
        self.add_parameter(FloatParameter('fft-weight', 25.0))
        self.fft = []

    def parameter_changed(self, parameter):
        pass

    def reset(self):
        self.locations = self.scene().get_all_pixel_locations()

    def draw(self, dt):

        def rotate(l, n):
            return l[n:] + l[:n]

        latest_fft = self._mixer.fft_data()

        if len(self.fft) == 0:
            self.fft.append(latest_fft)
            print "no fft"
            return

        self.fft.append(latest_fft)

        if len(self.fft) > 30:
            self.fft.pop(0)

        if False:
        #if self._mixer.is_onset():
            self._onset_decay = 1.0
        elif self._onset_decay > 0.0:
            self._onset_decay -= 0.05


        cx, cy = self.scene().center_point()
        x,y = (self.locations - (cx, cy)).T
        self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
        self.pixel_angles = np.arctan2(y, x) + math.pi
        self.pixel_distances /= max(self.pixel_distances)
        self.pixel_amplitudes = self.pixel_distances

        for pixel in range(len(self.pixel_amplitudes)):
            pixel_fft = int((1 - self.pixel_distances[pixel]) * (len(self.fft) - 1))
            fft = self.fft[pixel_fft]
            bin = int(self.pixel_angles[pixel] / (2.0 * math.pi) * len(fft))
            bin = np.mod(bin+1, len(fft))
            if bin < len(fft):
                self.pixel_amplitudes[pixel] = fft[bin] * self.parameter('fft-weight').get() * (1 - self.pixel_distances[pixel])


        angles = self.pixel_angles / (4.0 * math.pi)
        hues = np.abs(angles - 0.5)
        lights = (0.5 * self.pixel_amplitudes)
        hues = np.int_(np.mod(hues, 1.0) * self._fader_steps)
        colors = self._fader.color_cache[hues]
        colors = colors.T
        colors[0] = np.mod(colors[0], 1.0)
        colors[1] = lights
        colors = colors.T

        self._pixel_buffer = colors