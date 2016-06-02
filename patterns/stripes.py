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

import colorsys
import random
import math
import numpy as np
import ast

from lib.pattern import Pattern
from lib.parameters import FloatParameter, IntParameter, StringParameter
from lib.color_fade import ColorFade

class StripeGradient(Pattern):
    _fader = None

    def setup(self):
        self.add_parameter(FloatParameter('audio-brightness', 1.0))
        self.add_parameter(FloatParameter('audio-stripe-width', 100.0))
        self.add_parameter(FloatParameter('audio-speed', 0.0))
        self.add_parameter(FloatParameter('speed', 0.01))
        self.add_parameter(FloatParameter('angle-speed', 0.1))
        self.add_parameter(FloatParameter('stripe-width', 20))
        self.add_parameter(FloatParameter('center-orbit-distance', 200))
        self.add_parameter(FloatParameter('center-orbit-speed', 0.1))
        self.add_parameter(FloatParameter('hue-step', 0.1))
        self.add_parameter(IntParameter('posterization', 8))
        self.add_parameter(StringParameter('color-gradient', "[(0,0,1), (0,0,1), (0,1,1), (0,1,1), (0,0,1)]"))
        self.add_parameter(FloatParameter('stripe-x-center', 0.5))
        self.add_parameter(FloatParameter('stripe-y-center', 0.5))
        self.hue_inner = random.random() + 100
        self._center_rotation = random.random()
        self.stripe_angle = random.random()

        cx, cy = self.scene().center_point()
        self.locations = self.scene().get_all_pixel_locations()
        x,y = self.locations.T
        x -= cx
        y -= cy
        self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
        self.pixel_angles = (math.pi + np.arctan2(y, x)) / (2 * math.pi)
        self.pixel_distances /= max(self.pixel_distances)

        super(StripeGradient, self).setup()
            
    def parameter_changed(self, parameter):
        fade_colors = ast.literal_eval(self.parameter('color-gradient').get())
        self._fader = ColorFade(fade_colors, self.parameter('posterization').get())
    
    def reset(self):
        pass

    def draw(self, dt):
        if self._mixer.is_onset():
            self.hue_inner = self.hue_inner + self.parameter('hue-step').get()

        dt *= 1.0 + self.parameter('audio-speed').get() * self._mixer.audio.getLowFrequency()

        self.hue_inner += dt * self.parameter('speed').get()
        self._center_rotation += dt * self.parameter('center-orbit-speed').get()
        self.stripe_angle += dt * self.parameter('angle-speed').get()
        stripe_width = self.parameter('stripe-width').get() + self.parameter('audio-stripe-width').get() * self._mixer.audio.smoothEnergy
        cx, cy = self.scene().center_point()
        cx += math.cos(self._center_rotation) * self.parameter('center-orbit-distance').get()
        cy += math.sin(self._center_rotation) * self.parameter('center-orbit-distance').get()
        sx = self.parameter('stripe-x-center').get()
        sy = self.parameter('stripe-y-center').get()

        posterization = self.parameter('posterization').get()
        x, y = self.locations.T
        dx = x - cx
        dy = y - cy
        x = dx * math.cos(self.stripe_angle) - dy * math.sin(self.stripe_angle)
        y = dx * math.sin(self.stripe_angle) + dy * math.cos(self.stripe_angle)
        x = (x / stripe_width) % 1.0
        y = (y / stripe_width) % 1.0
        x = np.abs(x - sx)
        y = np.abs(y - sy)
        hues = np.int_(np.mod(x+y, 1.0) * posterization)
        colors = self._fader.color_cache[hues]
        colors.T[1] += self._mixer.audio.getEnergy() * self.parameter('audio-brightness').get()
        colors.T[0] += self.hue_inner
        self._pixel_buffer = colors
