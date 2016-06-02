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

    def setup(self):
        self.add_parameter(FloatTupleParameter('center', 2, (0.0, 0.0)))
        self.add_parameter(FloatParameter('speed', 0.1))
        self.add_parameter(StringParameter('color-gradient',
                                           '[(0,0,1), (0,1,1)]'))
        self.add_parameter(FloatParameter('spatial-freq', 1.5))

        self.hue_inner = random.random()

        self.locations = self.scene().get_all_pixel_locations()
        self.update_center()
        super(Concentric, self).setup()

        
    def update_center(self):
        x_offset, y_offset = self.parameter('center').get()
        xmin, ymin, xmax, ymax = self.scene().get_fixture_bounding_box()
        cx = ((1 - x_offset) * xmin + (1 + x_offset) * xmax) / 2.0
        cy = ((1 - y_offset) * ymin + (1 + y_offset) * ymax) / 2.0
        self.locations = self.scene().get_all_pixel_locations()

        x,y = self.locations.T
        x -= cx
        y -= cy
        self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
        self.pixel_distances /= max(self.pixel_distances)

    def parameter_changed(self, parameter):
        self.update_center()
        fade_colors = ast.literal_eval(self.parameter('color-gradient').get())
        self._fader = ColorFade(fade_colors, self._fader_steps)

    def reset(self):
        pass

    def draw(self, dt):
        self.hue_inner += dt * self.parameter('speed').get()

        hues = self.pixel_distances
        hues = np.fmod(self.hue_inner + hues * self.parameter('spatial-freq').get(), 1.0)
        luminances = [0.5] * (hues.size)
        saturations = [1.0] * (hues.size)

        self.setAllHLS(hues, luminances, saturations)
