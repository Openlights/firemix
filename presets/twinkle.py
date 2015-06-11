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

import random
import numpy as np
import ast

from lib.raw_preset import RawPreset
from lib.color_fade import ColorFade
from lib.parameters import FloatParameter, HLSParameter, StringParameter


class Twinkle(RawPreset):
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
        self.add_parameter(FloatParameter('birth-rate', 0.15))
        self.add_parameter(FloatParameter('fade-up-time', 0.5))
        self.add_parameter(FloatParameter('fade-down-time', 4.0))
        #self.add_parameter(HLSParameter('on-color', (0.1, 1.0, 1.0)))
        self.add_parameter(HLSParameter('off-color', (1.0, 0.0, 1.0)))
        self.add_parameter(FloatParameter('fade-rate', 0.1))
        self.add_parameter(HLSParameter('beat-color', (1.0, 1.0, 1.0)))
        self.add_parameter(FloatParameter('beat-births', 25.0))
        #self.add_parameter(HLSParameter('black-color', (0.0, 0.0, 1.0)))
        self.add_parameter(StringParameter('color-gradient', "[(0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (0.1, 1.0, 1.0)]"))
        self._setup_colors()
        self._nbirth = 0
        self._current_time = 0

    def parameter_changed(self, parameter):
        self._setup_colors()

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

    def draw(self, dt):

        self._current_time += dt

        # Birth
        if self._mixer.is_onset():
            self._nbirth += self.parameter('beat-births').get()

        # spawn FFT-colored stars
        if len(self._mixer.audio.fft[0]):
            fft_pixels = np.int_(np.multiply(self._mixer.audio.fft[0], self.parameter('audio-birth-rate').get() * self._mixer.audio.gain))
            births = np.sum(fft_pixels)
            popped, self._idle = self._idle[:births], np.append(self._idle[births:], self._idle[:births])
            colors = np.repeat(self._fader.color_cache[:256], fft_pixels, axis=0)

            # try lighting neighbors as well
            # for pixel in range(len(popped)):
            #     neighbors = self.scene().get_pixel_neighbors(popped[pixel])
            #     self.setPixelHLS(neighbors, colors[pixel])

            self.setPixelHLS(popped, colors)

        # spawn FFT-colored stars for max color only
        if len(self._mixer.audio.fft[0]):
            fft_pixels = np.atleast_1d(np.int_(np.multiply(self._mixer.audio.fft[0], self.parameter('audio-peak-birth-rate').get())))
            max = np.argmax(fft_pixels)
            births = fft_pixels[max]
            if births:
                popped = self._idle[:births]
                self._idle = np.append(self._idle[births:], popped)
                self.setPixelHLS(popped, self._fader.color_cache[max])

        # audioEnergy = self._mixer.audio.getEnergy() * self.parameter('audio-birth-rate').get() * dt
        # self._nbirth += audioEnergy

        self._nbirth += self.parameter('birth-rate').get() * dt

        black = self.parameter('off-color').get()
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


        # if len(self._fading_up) > 0:
        #     print self._fading_up, progress

        # dying
        # if len(self._fading_down):
        #     progress = np.atleast_1d(np.int_((1.0 - (self._current_time - self._time[self._fading_down]) / float(self.parameter('fade-down-time').get())) * self._fader_steps))
        #     colors = self._fader.color_cache[np.maximum(progress, 0)]
        #     self.setPixelHLS(self._fading_down, colors)
        #     finished = (progress <= 0)
        #     if len(finished):
        #         self._idle = np.append(self._idle, self._fading_down[finished])
        #         self._fading_down = np.delete(self._fading_down, finished)
        # elif self._mixer.is_onset():
        #     color = self.parameter('beat-color').get()
