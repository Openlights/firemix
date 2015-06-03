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

    def parameter_changed(self, parameter):
        pass

    def reset(self):
        self.locations = self.scene().get_all_pixel_locations()

    def draw(self, dt):

        def rotate(l, n):
            return l[n:] + l[:n]

        if False:
        #if self._mixer.is_onset():
            self._onset_decay = 1.0
        elif self._onset_decay > 0.0:
            self._onset_decay -= 0.05

        cx, cy = self.scene().center_point()
        x,y = (self.locations - (cx, cy)).T
        self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
        self.pixel_angles = np.mod((np.arctan2(y, x) + math.pi) / (math.pi * 2) + 1, 1)
        self.pixel_distances /= max(self.pixel_distances)
        self.pixel_amplitudes = self.pixel_distances

        fft = self._mixer.audio.fft

        if len(fft) == 0:
            return

        fft_size = len(fft[0])
        pixel_count = len(self.pixel_distances)

        time_to_graph = (len(fft) - 1) * (1 - self._mixer.audio.getEnergy() / 2)
        pixel_ffts = np.int_((self.pixel_distances) * time_to_graph)
        fft_per_pixel = np.asarray(fft)[pixel_ffts]
        bin_per_pixel = np.int_(self.pixel_angles * fft_size)
        self.pixel_amplitudes = fft_per_pixel[np.arange(pixel_count), bin_per_pixel]
        self.pixel_amplitudes = np.multiply(self.pixel_amplitudes, self.parameter('fft-weight').get() * (1 - self.pixel_distances))

        # angle_bin_width = (2.0 * math.pi) / len(fft[0])
        # for bin in range(len(fft[0])):
        #     start = bin * angle_bin_width
        #     end = (bin + 0.5) * angle_bin_width
        #     mask = (self.pixel_angles > start) & (self.pixel_angles < end) & (self.pixel_distances < fft[0][bin])
        #     self.pixel_amplitudes[mask] += 0.3

        self.setAllHLS(self.pixel_angles, (0.5 * self.pixel_amplitudes), 1.0)