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

from noise import snoise3
import numpy as np
import ast

from profilehooks import profile

from lib.color_fade import ColorFade
from lib.pattern import Pattern
from lib.parameters import FloatParameter, IntParameter, StringParameter
import math
from lib.colors import clip

class SimplexNoise(Pattern):
    """
    Simplex noise hue map
    """

    _luminance_steps = 256
    
    def setup(self):
        self.add_parameter(FloatParameter('audio-brightness', 0.0))
        self.add_parameter(FloatParameter('hue-min', 0.0))
        self.add_parameter(FloatParameter('hue-max', 3.0))
        self.add_parameter(FloatParameter('hue-offset', 0.0))
        self.add_parameter(FloatParameter('audio-hue-offset', 0.0))
        self.add_parameter(FloatParameter('speed', 0.7))
        self.add_parameter(FloatParameter('angle', 0.125))
        self.add_parameter(FloatParameter('color-speed', 0.2))
        self.add_parameter(IntParameter('resolution', 128))
        self.add_parameter(FloatParameter('scale', 0.25))
        self.add_parameter(FloatParameter('stretch', 1.0))
        self.add_parameter(FloatParameter('luminance-scale', 0.75))
        self.add_parameter(StringParameter('luminance-map', "[(0,0,1), (0,0,1), (0,1,1)]"))
        self.add_parameter(FloatParameter('beat-lum-boost', 0.05))
        self.add_parameter(FloatParameter('beat-lum-time', 0.1))
        self.add_parameter(FloatParameter('beat-color-boost', 0.0))
        self._offset_x = 0
        self._offset_y = 0
        self._offset_z = 0
        
        self.pixel_locations = np.asarray(self.scene().get_all_pixel_locations())

        self.color_lookup = {}
        self._setup_pars()

        super(SimplexNoise, self).setup()

    def parameter_changed(self, parameter):
        self._setup_pars()

    def reset(self):
        self._setup_pars()

    def _setup_pars(self):
        self.hue_min = self.parameter('hue-min').get()
        self.hue_max = self.parameter('hue-max').get()
        self.color_speed = self.parameter('color-speed').get()
        self.scale = self.parameter('scale').get() / 100.0
        fade_colors = ast.literal_eval(self.parameter('luminance-map').get())
        self.lum_fader = ColorFade(fade_colors, self._luminance_steps)

    @profile
    def draw(self, dt):
        if self._mixer.is_onset():
            self._offset_z += self.parameter('beat-color-boost').get()

        angle = self.parameter('angle').get()
        #self._offset_x += dt * self.parameter('speed').get() * math.cos(angle) * 2 * math.pi
        #self._offset_y += dt * self.parameter('speed').get() * math.sin(angle) * 2 * math.pi
        self._offset_x += dt * self.parameter('speed').get()
        self._offset_z += dt * self.parameter('color-speed').get()
        self._offset_z += dt * self._mixer.audio.getSmoothEnergy() * self.parameter('beat-color-boost').get()
        # posterization = self.parameter('resolution').get()

        rotMatrix = np.array([(math.cos(angle), -math.sin(angle)), (math.sin(angle),  math.cos(angle))])
        x,y = rotMatrix.T.dot(self.pixel_locations.T)
        x *= self.parameter('stretch').get()
        x += self._offset_x
        y += self._offset_y
        locations = np.asarray([x,y]).T

        luminance_scale = self.parameter('luminance-scale').get() / 100.0
        brights = np.asarray([snoise3(luminance_scale * location[0], luminance_scale * location[1], self._offset_z, 1, 0.5, 0.5) for location in locations])
        brights = (1.0 + brights) / 2
        brights *= self._luminance_steps
        LS = self.lum_fader.color_cache[np.int_(brights)].T
        luminances = LS[1] + self._mixer.audio.getEnergy() * self.parameter('audio-brightness').get()
        hue_offset = self.parameter('hue-offset').get() + self._mixer.audio.getSmoothEnergy() * self.parameter('audio-hue-offset').get()

        self.setAllHLS(LS[0] + hue_offset, luminances, LS[2])

