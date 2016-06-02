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
import ast

from lib.pattern import Pattern
from lib.parameters import FloatParameter, StringParameter
from lib.watch import Watch
from lib.color_fade import ColorFade
from scipy import signal

class TestFFT(Pattern):
    """Simple test for FFT data coming from aubio"""

    _fader = None
    _fader_steps = 256
    _onset_decay = 0.0

    def setup(self):
        self.add_parameter(FloatParameter('fft-weight', 25.0))
        self.add_parameter(FloatParameter('fft-bias', 0.0))
        self.add_parameter(FloatParameter('fft-gamma', 1.0))
        self.add_parameter(FloatParameter('rotation', 0.0))
        self.add_parameter(StringParameter('color-gradient', "[(0,0.5,1), (1,0.5,1)]"))
        self.add_parameter(FloatParameter('frequency-max', 1.0))
        self.add_parameter(FloatParameter('frequency-min', 0.0))
        self.add_parameter(FloatParameter('time-range', 1.0))
        self.add_parameter(FloatParameter('pie-peaks', 0.0))
        self.add_parameter(FloatParameter('rings', 0.0))
        self.add_parameter(FloatParameter('linear', 0.0))
        self.add_parameter(FloatParameter('linear-weight', 2.0))
        self.add_parameter(FloatParameter('ring bars', 0.0))
        self.add_parameter(FloatParameter('ring peaks', 0.0))
        self.add_parameter(FloatParameter('ring peak width', 0.02))
        self.add_parameter(FloatParameter('ring current', 0.0))
        self.add_parameter(FloatParameter('ghosting', 0.0))
        self.add_parameter(FloatParameter('noise threshold', 0.1))
        self.add_parameter(FloatParameter('fft smoothing', 1.0))

        self.color_angle = 0.0
        self.add_watch(Watch(self, 'color_angle'))

        super(TestFFT, self).setup()

    def parameter_changed(self, parameter):
        fade_colors = ast.literal_eval(self.parameter('color-gradient').get())
        self._fader = ColorFade(fade_colors, self._fader_steps)

    def reset(self):
        self.locations = self.scene().get_all_pixel_locations()
        self.color_angle = 0.0

    def draw(self, dt):

        def rotate(l, n):
            return l[n:] + l[:n]

        self.color_angle += dt *  self.parameter('rotation').get()

        if False:
        #if self._mixer.is_onset():
            self._onset_decay = 1.0
        elif self._onset_decay > 0.0:
            self._onset_decay -= 0.05

        cx, cy = self.scene().center_point()
        x,y = (self.locations - (cx, cy)).T
        self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
        self.pixel_angles = np.mod((np.arctan2(y, x) + (self.color_angle * math.pi)) / (math.pi * 2) + 1, 1)
        self.pixel_distances /= np.max(self.pixel_distances)
        self.pixel_amplitudes = self.pixel_distances

        fft = self._mixer.audio.fft_data()

        if len(fft) == 0:
            return

        fft_size = len(fft[0])
        pixel_count = len(self.pixel_distances)
        self.pixel_amplitudes = np.zeros(pixel_count)

        noise_threshold = self.parameter('noise threshold').get()
        smooth_fft = self._mixer.audio.getSmoothedFFT()

        if len(smooth_fft):
            if self.parameter('fft smoothing').get():
                np.maximum(smooth_fft - noise_threshold, 0, smooth_fft)
                np.multiply(smooth_fft, 1.0 / (1.0 - noise_threshold), smooth_fft)
                convolution = signal.gaussian(self.parameter('fft smoothing').get(), std=1.0)

                smooth_fft = np.convolve(smooth_fft, convolution, 'same')

        if self.parameter('fft-weight').get():
            #time_to_graph = (len(fft) - 1) * (1 - self._mixer.audio.getEnergy() / 2) # pulse with total energy
            frequency_min = self.parameter('frequency-min').get()
            frequency_max = self.parameter('frequency-max').get()
            frequency_range = frequency_max - frequency_min
            time_to_graph = (len(fft) - 1) * self.parameter('time-range').get()
            pixel_ffts = np.mod(np.int_((self.pixel_distances) * time_to_graph), len(fft))
            fft_per_pixel = np.asarray(fft)[pixel_ffts]
            bin_per_pixel = np.int_(np.mod(self.pixel_angles * frequency_range + frequency_min, 1.0) * fft_size)
            self.pixel_amplitudes = fft_per_pixel[np.arange(pixel_count), bin_per_pixel]
            self.pixel_amplitudes = np.multiply(self.pixel_amplitudes, self.parameter('fft-weight').get() * (1 - self.pixel_distances))

        hues = np.int_(np.mod(self.pixel_angles, 1.0) * self._fader_steps)

        if self.parameter('ring current').get():
            np.minimum(self.pixel_distances, 1.0, self.pixel_distances)
            pd = np.int_((self.pixel_distances * 1.2 - 0.1) * (fft_size - 1))
            np.minimum(pd, fft_size - 1, pd)
            np.maximum(pd, 0.0, pd)
            mask = (self.pixel_angles > (1.0 - fft[0][pd]))
            self.pixel_amplitudes[mask] += self.parameter('ring current').get()

        if len(smooth_fft):
            if self.parameter('pie-peaks').get():
                mask = (self.pixel_distances < smooth_fft[np.int_(self.pixel_angles * len(smooth_fft))])
                self.pixel_amplitudes[mask] += self.parameter('pie-peaks').get()

            if self.parameter('rings').get():
                pd = np.int_(len(smooth_fft) * (1.2 * self.pixel_distances - 0.1))
                np.minimum(pd, len(smooth_fft) - 1, pd)
                np.maximum(pd, 0.0, pd)
                self.pixel_amplitudes += smooth_fft[pd] * self.parameter('rings').get()
                hues = pd

            if self.parameter('ring bars').get():
                pd = np.int_(len(smooth_fft) * (1.2 * self.pixel_distances - 0.1))
                np.minimum(pd, len(smooth_fft) - 1, pd)
                np.maximum(pd, 0.0, pd)
                mask = (self.pixel_angles < smooth_fft[pd])
                self.pixel_amplitudes[mask] += self.parameter('ring bars').get()

            if self.parameter('ring peaks').get():
                pd = np.int_(len(smooth_fft) * (1.1 * self.pixel_distances))
                np.minimum(pd, len(smooth_fft) - 1, pd)
                np.maximum(pd, 0.0, pd)
                peak_width = self.parameter('ring peak width').get()
                mask = (np.abs(self.pixel_angles - smooth_fft[pd]) < peak_width)
                self.pixel_amplitudes[mask] += self.parameter('ring peaks').get()

            if self.parameter('linear').get():
                x -= np.min(x)
                x /= np.max(x)
                #y -= np.min(y)
                y /= np.max(y)
                pd = np.int_(len(smooth_fft) * (x))
                np.minimum(pd, len(smooth_fft) - 1, pd)
                np.maximum(pd, 0.0, pd)
                mask = (np.abs(y) < smooth_fft[pd] * self.parameter('linear-weight').get())
                self.pixel_amplitudes[mask] += self.parameter('linear').get()
                hues = pd

        colors = self._fader.color_cache[hues]
        np.minimum(self.pixel_amplitudes, 1, self.pixel_amplitudes)
        colors.T[1] *= np.power(self.pixel_amplitudes - self.parameter('fft-bias').get(), self.parameter('fft-gamma').get())
        colors.T[1] = self._pixel_buffer.T[1] * self.parameter('ghosting').get() + colors.T[1]

        self._pixel_buffer = colors
