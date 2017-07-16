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
from lib.colors import clip
from lib.parameters import FloatTupleParameter, FloatParameter, StringParameter
from lib.color_fade import ColorFade

class Concentric(Pattern):
    """Radial gradient that responds to onsets"""
    _fader_steps = 256
    random_point = lambda self: np.array((random.uniform(-0.85, 0.85),
                                          random.uniform(-0.85, 0.85)))

    def setup(self):
        #self.add_parameter(FloatTupleParameter('center', 2, (0.0, 0.0)))
        self.add_parameter(FloatParameter('color-speed', 0.1))
        self.add_parameter(FloatParameter('max-speed', 1.0))
        self.add_parameter(FloatParameter('deceleration', 0.01))
        self.add_parameter(StringParameter('color-gradient',
                                           '[(0,0.5,1), (1,0.5,1)]'))
        self.add_parameter(FloatParameter('spatial-freq', 1.5))

        self.hue_inner = random.random()

        self.locations = self.scene().get_all_pixel_locations()
        self.bounding_box = self.scene().get_fixture_bounding_box()

        self.center = self.random_point()
        self.target = self.random_point()
        self.heading = self.target - self.center
        self.heading /= np.linalg.norm(self.heading)
        self.center_speed = self.parameter('max-speed').get() / 10.0

        self.update_center()


    def update_center(self):
        x_offset, y_offset = self.center
        xmin, ymin, xmax, ymax = self.bounding_box
        cx = ((1 - x_offset) * xmin + (1 + x_offset) * xmax) / 2.0
        cy = ((1 - y_offset) * ymin + (1 + y_offset) * ymax) / 2.0

        x,y = np.copy(self.locations.T)
        x -= cx
        y -= cy
        self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
        self.pixel_distances /= ((xmax - xmin) / 2.0)

    def parameter_changed(self, parameter):
        fade_colors = ast.literal_eval(self.parameter('color-gradient').get())
        self._fader = ColorFade(fade_colors, self._fader_steps)

    def tick(self, dt):
        super(Concentric, self).tick(dt)
        self.walk(dt)
        self.update_center()
        self.hue_inner += dt * self.parameter('color-speed').get()

    def draw(self):
        hues = self.pixel_distances
        hues = np.fmod(self.hue_inner + hues * self.parameter('spatial-freq').get(), 1.0)
        hues = np.int_(np.mod(hues, 1.0) * self._fader_steps)
        colors = self._fader.color_cache[hues]
        self._pixel_buffer = colors

    def at_target(self, epsilon):
      return np.linalg.norm(self.center - self.target) < epsilon

    def walk(self, dt):
      step_size = dt * self.center_speed
      if np.linalg.norm(self.center) > 1 or self.center_speed < dt:
        self.center_speed = self.parameter('max-speed').get()
        self.target = self.random_point()
        self.heading = self.target - self.center
        self.heading /= np.linalg.norm(self.heading)
      self.center += step_size * self.heading
      self.center_speed *= (1 - self.parameter('deceleration').get())
