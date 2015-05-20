# This file is part of Firemix.
#
# Copyright 2013-2015 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

import random

from lib.raw_preset import RawPreset
from lib.color_fade import ColorFade
from lib.parameters import FloatParameter, HLSParameter


class Twinkle(RawPreset):
    """Random pixels fade in and out"""

    _fading_up = []
    _fading_down = []
    _time = {}
    _fader = None
    _fader_steps = 256

    def setup(self):
        random.seed()
        self.add_parameter(FloatParameter('birth-rate', 0.15))
        self.add_parameter(FloatParameter('fade-up-time', 0.5))
        self.add_parameter(FloatParameter('fade-down-time', 4.0))
        self.add_parameter(HLSParameter('on-color', (0.1, 1.0, 1.0)))
        self.add_parameter(HLSParameter('off-color', (1.0, 0.0, 1.0)))
        self.add_parameter(HLSParameter('beat-color', (1.0, 1.0, 1.0)))
        self.add_parameter(FloatParameter('beat-births', 25.0))
        self.add_parameter(HLSParameter('black-color', (0.0, 0.0, 1.0)))
        self._setup_colors()
        self._nbirth = 0
        self._current_time = 0

    def parameter_changed(self, parameter):
        self._setup_colors()

    def _setup_colors(self):
        self._fader = ColorFade([self.parameter('black-color').get(), self.parameter('off-color').get(), self.parameter('on-color').get()], self._fader_steps)

    def reset(self):
        self._fading_up = []
        self._fading_down = []
        self._idle = self.scene().get_all_pixels()[:]
        self._time = {}

    def draw(self, dt):

        self._current_time += dt

        # Birth
        if self._mixer.is_onset():
            self._nbirth += self.parameter('beat-births').get()
        
        self._nbirth += self.parameter('birth-rate').get() * dt

        for i in range(int(self._nbirth)):
            if random.random() < self._nbirth:
                if (len(self._idle) > 0):
                    address = self._idle.pop(random.randint(0, len(self._idle) - 1))
                    self._fading_up.append(address)
                    self._time[address] = self._current_time
                self._nbirth -= 1

        # Growth
        for address in self._fading_up:
            progress = (self._current_time - self._time[address]) / float(self.parameter('fade-up-time').get()) * self._fader_steps
            color = self._fader.get_color(progress)
            if progress >= self._fader_steps:
                self._fading_up.remove(address)
                self._fading_down.append(address)
                self._time[address] = self._current_time
            self.setPixelHLS(address, color)

        # Decay
        for address in self._fading_down:
            progress = (1.0 - (self._current_time - self._time[address]) / float(self.parameter('fade-down-time').get())) * self._fader_steps
            color = self._fader.get_color(progress)
            if progress <= 0:
                self._idle.append(address)
                self._fading_down.remove(address)
            elif self._mixer.is_onset():
                color = self.parameter('beat-color').get()
            self.setPixelHLS(address, color)