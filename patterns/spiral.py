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
import colorsys
import random
import math
import ast

from lib.pattern import Pattern
from lib.parameters import FloatParameter, HLSParameter, StringParameter
from lib.color_fade import ColorFade

class SpiralGradient(Pattern):
    """Spiral gradient that responds to onsets"""
       
    _fader = None
    _fader_steps = 256
    
    def setup(self):
        self.add_parameter(FloatParameter('audio-brightness', 0.0))
        self.add_parameter(FloatParameter('audio-twist', 0.0))
        self.add_parameter(FloatParameter('audio-speed-boost-bass', 0.0))
        self.add_parameter(FloatParameter('audio-speed-boost-treble', 0.0))
        self.add_parameter(FloatParameter('speed', 0.3))
        self.add_parameter(FloatParameter('hue-speed', 0.3))
        self.add_parameter(FloatParameter('angle-hue-width', 2.0))
        self.add_parameter(FloatParameter('radius-hue-width', 1.5))        
        self.add_parameter(FloatParameter('wave-hue-width', 0.1))        
        self.add_parameter(FloatParameter('wave-hue-period', 0.1))        
        self.add_parameter(FloatParameter('wave-speed', 0.1))        
        self.add_parameter(FloatParameter('onset-speed-boost', 5.0))
        self.add_parameter(FloatParameter('onset-speed-decay', 1.0))
        self.add_parameter(StringParameter('color-gradient', "[(0,0,1), (0,1,1)]"))
        self.add_parameter(FloatParameter('center-distance', 0.0))
        self.add_parameter(FloatParameter('center-speed', 0.0))
        self.add_parameter(FloatParameter('audio-wave-period-boost', 0.0))
        self.add_parameter(FloatParameter('wave-falloff', 0.0))
        self.hue_inner = 0
        self.color_offset = 0
        self.wave_offset = random.random()

        self.center_offset_angle = 0

        self.onset_speed_boost = 1

        self.audio_twist = 0

        super(SpiralGradient, self).setup()

    def parameter_changed(self, parameter):
        fade_colors = ast.literal_eval(self.parameter('color-gradient').get())
        self._fader = ColorFade(fade_colors, self._fader_steps)

    def reset(self):
        self.locations = self.scene().get_all_pixel_locations()

    def draw(self, dt):
        if self._mixer.is_onset():
            self.onset_speed_boost = self.parameter('onset-speed-boost').get()

        self.color_offset += dt * self._mixer.audio.getLowFrequency() * self.parameter('audio-speed-boost-bass').get()
        self.color_offset += dt * self._mixer.audio.getHighFrequency() * self.parameter('audio-speed-boost-treble').get()

        self.center_offset_angle += dt * self.parameter('center-speed').get()
        self.hue_inner += dt * self.parameter('hue-speed').get() * self.onset_speed_boost
        self.wave_offset += dt * self.parameter('wave-speed').get() * self.onset_speed_boost
        self.color_offset += dt * self.parameter('speed').get() * self.onset_speed_boost

        self.onset_speed_boost = max(1, self.onset_speed_boost - self.parameter('onset-speed-decay').get())

        wave_hue_period = 2 * math.pi * self.parameter('wave-hue-period').get() + self.parameter('audio-wave-period-boost').get() * self._mixer.audio.getEnergy()
        wave_hue_width = self.parameter('wave-hue-width').get()
        radius_hue_width = self.parameter('radius-hue-width').get()
        angle_hue_width = self.parameter('angle-hue-width').get()

        cx, cy = self.scene().center_point()

        center_distance = self.parameter('center-distance').get()
        x,y = (self.locations - (cx + math.cos(self.center_offset_angle) * center_distance,
                                  cy + math.sin(self.center_offset_angle) * center_distance)).T
        self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
        self.pixel_angles = np.arctan2(y, x) / (2.0 * math.pi)
        self.pixel_distances /= max(self.pixel_distances)
        wave_amplitude = self.pixel_distances
        wave_falloff = self.parameter('wave-falloff').get()
        if wave_falloff !=0:
            wave_amplitude *= np.max(wave_falloff - self.pixel_distances, 0)

        self.audio_twist *= 0.9
        self.audio_twist += + self.parameter('audio-twist').get() * self._mixer.audio.getLowFrequency()

        angles = np.mod(1.0 - self.pixel_angles - np.sin(self.wave_offset + wave_amplitude * wave_hue_period) * (wave_hue_width + self.audio_twist), 1.0)
        hues = self.color_offset + (radius_hue_width * self.pixel_distances) + (2 * np.abs(angles - 0.5) * angle_hue_width)
        hues = np.int_(np.mod(hues, 1.0) * self._fader_steps)
        colors = self._fader.color_cache[hues]
        colors = colors.T
        colors[0] = np.mod(colors[0] + self.hue_inner, 1.0)
        colors[1] += self._mixer.audio.getEnergy() * self.parameter('audio-brightness').get()
        colors = colors.T

        self._pixel_buffer = colors
