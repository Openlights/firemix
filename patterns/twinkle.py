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

import random
import numpy as np
import ast
import math

from lib.pattern import Pattern
from lib.color_fade import ColorFade
from lib.parameters import FloatParameter, HLSParameter, StringParameter


class Twinkle(Pattern):
    """Random pixels fade in and out"""

    _fading_up = []
    _fading_down = []
    _time = {}
    _fader = None
    _fader_steps = 256

    def setup(self):
        random.seed()
        self.add_parameter(FloatParameter('audio-birth-rate', 0.0))
        self.add_parameter(FloatParameter('audio-peak-birth-rate', 0.0))
        self.add_parameter(FloatParameter('audio-ring-birth-rate', 0.0))
        self.add_parameter(FloatParameter('audio-ring-width', 5.0))
        self.add_parameter(FloatParameter('audio-ring-lifetime', 2.0))
        self.add_parameter(FloatParameter('audio-ring-diameter', 300.0))
        self.add_parameter(FloatParameter('audio-ring-start-radius', 0.0))
        self.add_parameter(FloatParameter('audio-ring-use-fft-brightness', 0.0))
        self.add_parameter(FloatParameter('audio-eq-bands', 0.0))
        self.add_parameter(FloatParameter('noise threshold', 0.1))
        self.add_parameter(FloatParameter('birth-rate', 0.15))
        self.add_parameter(FloatParameter('fade-up-time', 0.5))
        self.add_parameter(FloatParameter('fade-down-time', 4.0))
        self.add_parameter(FloatParameter('fade-rate', 0.1))
        self.add_parameter(HLSParameter('beat-color', (1.0, 1.0, 1.0)))
        self.add_parameter(FloatParameter('beat-births', 25.0))
        #self.add_parameter(HLSParameter('black-color', (0.0, 0.0, 1.0)))
        self.add_parameter(StringParameter('color-gradient', "[(0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (0.1, 1.0, 1.0)]"))
        self.add_parameter(FloatParameter('pie-peaks', 0.0))
        self._setup_colors()
        self._nbirth = 0
        self._current_time = 0
        self.birthByFFT = np.zeros(256)

        super(Twinkle, self).setup()

    def parameter_changed(self, parameter):
        self._setup_colors()
        self.eq_centers = self._idle[:int(self.parameter('audio-eq-bands').get())]

    def _setup_colors(self):
        #fade_colors = [self.parameter('black-color').get(), self.parameter('off-color').get(), self.parameter('on-color').get()]
        fade_colors = ast.literal_eval(self.parameter('color-gradient').get())
        self._fader = ColorFade(fade_colors, self._fader_steps)
        #self.add_parameter(StringParameter('color-gradient', str(fade_colors)))

    def reset(self):
        self._fading_up =  np.empty([0], dtype=int)
        self._fading_down =  np.empty([0], dtype=int)
        self._idle = np.asarray(self.scene().get_all_pixels()[:])
        np.random.shuffle(self._idle)
        self._time = np.zeros((len(self._idle)))
        self.color_angle = 0
        self.ringTimes = np.zeros(len(self.scene().get_all_pixels()))
        self.ringColors = np.zeros(len(self.scene().get_all_pixels()))
        self.locations = self.scene().get_all_pixel_locations()
        self.birthByFFT = np.zeros(256)

    def draw(self, dt):

        self._current_time += dt

        # Birth
        if self._mixer.is_onset():
            self._nbirth += self.parameter('beat-births').get()

        # spawn FFT-colored stars
        fft = self._mixer.audio.fft_data()[0]
        noise_threshold = self.parameter('noise threshold').get()
        np.maximum(fft - noise_threshold, 0, fft)
        np.multiply(fft, 1.0 / (1.0 - noise_threshold), fft)

        if len(fft):
            self.birthByFFT += np.multiply(fft, self.parameter('audio-birth-rate').get())
            fft_pixels = np.int_(self.birthByFFT)
            births = np.sum(fft_pixels)
            self.birthByFFT -= fft_pixels
            popped, self._idle = self._idle[:births], np.append(self._idle[births:], self._idle[:births])
            colors = np.repeat(self._fader.color_cache[:256], fft_pixels, axis=0)

            self.setPixelHLS(popped, colors[:len(popped)])

        # spawn FFT-colored rings
        if len(fft):
            # fft_pixels = np.atleast_1d(np.int_(np.multiply(fft, self.parameter('audio-ring-birth-rate').get())))
            # max = np.argmax(fft_pixels)
            # births = fft_pixels[max]
            self.birthByFFT += np.multiply(fft, self.parameter('audio-ring-birth-rate').get())
            fft_pixels = np.int_(self.birthByFFT)
            births = np.sum(fft_pixels)
            self.birthByFFT -= fft_pixels

            if births:
                popped = self._idle[:births]
                self.ringTimes[popped] = self._current_time
                colors = np.repeat(np.arange(256), fft_pixels, axis=0)

                self.ringColors[popped] = colors
                self._idle = np.append(self._idle[births:], popped)

            currentTimes = self._current_time - self.ringTimes
            ringLife = self.parameter('audio-ring-lifetime').get()
            for pixel in np.where(currentTimes < ringLife)[0]:
                if self.ringTimes[pixel] > 0:
                    #print pixel
                    ringWidth = self.parameter('audio-ring-width').get()
                    size_percent = currentTimes[np.int_(pixel)] / ringLife
                    ring = np.where(np.abs(self.parameter('audio-ring-diameter').get() * size_percent + self.parameter('audio-ring-start-radius').get() - self.scene().get_pixel_distances(np.int_(pixel))) < ringWidth)
                    color = self._fader.color_cache[self.ringColors[pixel]]

                    # if self.parameter('audio-ring-use-fft-brightness').get():
                    #     # self._mixer.audio.getSmoothedFFT()[self.ringColors[pixel]]
                    #     color[1] += self._mixer.audio.getEnergy() * self.parameter('audio-ring-use-fft-brightness').get()

                    self._pixel_buffer.T[0][ring] = color[0]
                    self._pixel_buffer.T[1][ring] += color[1] * (1.0 - currentTimes[pixel] / ringLife)
                    self._pixel_buffer.T[2][ring] = color[2]

                    #self.setPixelHLS(ring, color)

        # ring eq
        if len(fft):
            smooth_fft = self._mixer.audio.getSmoothedFFT()
            if len(smooth_fft):
                eq_bands = self.parameter('audio-eq-bands').get()
                if eq_bands:
                    band_size = np.int_(len(smooth_fft) / eq_bands)
                    for band in range(np.int_(eq_bands)):
                        neighbors = self.scene().get_pixel_neighbors(self.eq_centers[band])
                        self.eq_centers[band] = neighbors[np.int_(np.random.random() * len(neighbors))]
                        fft_amount = np.sum(smooth_fft[band * band_size : (band + 1) * band_size]) / band_size
                        pixel = self.eq_centers[band]
                        color_band_size = np.int_(len(self._fader.color_cache) / eq_bands)
                        color = self._fader.color_cache[np.int_((band + 0.5) * color_band_size)]
                        ringWidth = self.parameter('audio-ring-width').get()
                        size_percent = fft_amount
                        ring = np.where(np.abs(self.parameter('audio-ring-diameter').get() * size_percent + self.parameter('audio-ring-start-radius').get() - self.scene().get_pixel_distances(np.int_(pixel))) < ringWidth)
                        self._pixel_buffer.T[0][ring] = color[0]
                        self._pixel_buffer.T[1][ring] += color[1] * fft_amount
                        self._pixel_buffer.T[2][ring] = color[2]

        # spawn FFT-colored stars  for max color only
        if len(fft):
            fft_pixels = np.atleast_1d(np.int_(np.multiply(fft, self.parameter('audio-peak-birth-rate').get())))
            max = np.argmax(fft_pixels)
            births = fft_pixels[max]
            if births:
                popped = self._idle[:births]
                self._idle = np.append(self._idle[births:], popped)
                self.setPixelHLS(popped, self._fader.color_cache[max])

            # this doesn't belong here, just testing
            if self.parameter('pie-peaks').get():
                self.locations = self.scene().get_all_pixel_locations()
                cx, cy = self.scene().center_point()
                x,y = (self.locations - (cx, cy)).T
                self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
                self.color_angle += 0.001
                self.pixel_angles = np.mod((np.arctan2(y, x) + (self.color_angle * math.pi)) / (math.pi * 2) + 1, 1)
                self.pixel_distances /= np.max(self.pixel_distances)
                mask = (self.pixel_distances < 2 * fft[np.int_(self.pixel_angles * len(fft))])
                self._pixel_buffer.T[1][mask] = self.parameter('pie-peaks').get()

        # audioEnergy = self._mixer.audio.getEnergy() * self.parameter('audio-birth-rate').get() * dt
        # self._nbirth += audioEnergy

        self._nbirth += self.parameter('birth-rate').get() * dt

        #black = self.parameter('off-color').get()
        fade_rate = self.parameter('fade-rate').get()

        self._pixel_buffer.T[1] *= (1.0 - fade_rate)
        #np.multiply(self._pixel_buffer, (1.0 - fade_rate), self._pixel_buffer)

        # birthing
        births = int(self._nbirth)
        if births > 0:
            popped, self._idle = self._idle[:births], self._idle[births:]
            self._fading_up = np.append(self._fading_up, popped)
            self._time[popped] = self._current_time
            self._nbirth -= births

        # growing
        if len(self._fading_up):
            progress = np.atleast_1d(np.int_((self._current_time - self._time[self._fading_up]) / float(self.parameter('fade-up-time').get()) * self._fader_steps))
            colors = self._fader.color_cache[np.minimum(progress, self._fader_steps)]
            self.setPixelHLS(self._fading_up, colors)
            finished = (progress >= self._fader_steps)
            if len(self._fading_up[finished]) > 0:
                self._idle = np.append(self._idle, self._fading_up[finished])
                self._fading_up = self._fading_up[np.logical_not(finished)]
                self._time[finished] = self._current_time
