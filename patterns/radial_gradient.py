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
from lib.parameters import FloatParameter, StringParameter
from lib.color_fade import ColorFade

class RadialGradient(Pattern):
    """Radial gradient that responds to onsets"""
    _luminance_steps = 256
    _fader_steps = 256

    def setup(self):
        self.add_parameter(FloatParameter('speed', 0.1))
        self.add_parameter(FloatParameter('hue-width', 1.5))
        self.add_parameter(FloatParameter('hue-step', 0.1))    
        self.add_parameter(FloatParameter('wave1-amplitude', 0.5))
        self.add_parameter(FloatParameter('wave1-period', 1.5))
        self.add_parameter(FloatParameter('wave1-speed', 0.05))
        self.add_parameter(FloatParameter('wave2-amplitude', 0.5))
        self.add_parameter(FloatParameter('wave2-period', 1.5))
        self.add_parameter(FloatParameter('wave2-speed', 0.1))
        self.add_parameter(FloatParameter('rwave-amplitude', 0.5))
        self.add_parameter(FloatParameter('rwave-standing', 0.0))
        self.add_parameter(FloatParameter('rwave-period', 1.5))
        self.add_parameter(FloatParameter('rwave-speed', 0.1))
        self.add_parameter(FloatParameter('radius-scale', 1.0))
        self.add_parameter(FloatParameter('audio-radius-scale', 0.0))
        self.add_parameter(FloatParameter('audio-amplitude', 0.0))
        self.add_parameter(FloatParameter('audio-boost', 0.0))
        self.add_parameter(FloatParameter('audio-brightness', 0.0))
        self.add_parameter(FloatParameter('audio-scale', 0.0))
        self.add_parameter(FloatParameter('audio-use-fader', 0.0))
        self.add_parameter(FloatParameter('audio-energy-lum-time', 0.0))
        self.add_parameter(FloatParameter('audio-energy-lum-strength', 0.0))
        self.add_parameter(FloatParameter('audio-fader-percent', 1.0))
        self.add_parameter(FloatParameter('luminance-speed', 0.01))
        self.add_parameter(FloatParameter('luminance-scale', 1.0))
        self.add_parameter(StringParameter('color-gradient', "[(0,0,1), (0,1,1)]"))

        self.hue_inner = random.random()
        self.wave1_offset = 0 #andom.random()
        self.wave2_offset = random.random()
        self.rwave_offset = random.random()
        self.luminance_offset = random.random()

        cx, cy = self.scene().center_point()

        self.locations = self.scene().get_all_pixel_locations()
        x,y = self.locations.T
        x -= cx
        y -= cy
        self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
        self.pixel_angles = math.pi + np.arctan2(y, x)
        self.pixel_distances /= max(self.pixel_distances)

        super(RadialGradient, self).setup()
        
    def parameter_changed(self, parameter):
        fade_colors = ast.literal_eval(self.parameter('color-gradient').get())
        self._fader = ColorFade(fade_colors, self._fader_steps)

    def reset(self):
        pass

    def draw(self, dt):
        if self._mixer.is_onset():
            self.hue_inner = math.fmod(self.hue_inner + self.parameter('hue-step').get(), 1.0)
            self.luminance_offset += self.parameter('hue-step').get()

        dt *= 1.0 + self.parameter('audio-boost').get() * self._mixer.audio.getLowFrequency()
        self.hue_inner += dt * self.parameter('speed').get()
        self.wave1_offset += self.parameter('wave1-speed').get() * dt
        self.wave2_offset += self.parameter('wave2-speed').get() * dt
        self.rwave_offset += self.parameter('rwave-speed').get() * dt
        self.luminance_offset += self.parameter('luminance-speed').get() * dt

        luminance_scale = self.parameter('luminance-scale').get() + self._mixer.audio.smoothEnergy * self.parameter('audio-scale').get()
        if self.parameter('rwave-standing').get():
            rwave = np.sin(self.pixel_distances * self.parameter('rwave-period').get()) * self.parameter('rwave-standing').get() * np.sin(self.rwave_offset)
            rwave += np.sin(self.rwave_offset + np.pi * 0.75) * self.parameter('rwave-standing').get()
        else:
            rwave = np.abs(np.sin(self.rwave_offset + self.pixel_distances * self.parameter('rwave-period').get()) * self.parameter('rwave-amplitude').get())
        pixel_angles = self.pixel_angles + rwave

        wave1 = np.abs(np.cos(self.wave1_offset + pixel_angles * self.parameter('wave1-period').get()) * self.parameter('wave1-amplitude').get())
        wave2 = np.abs(np.cos(self.wave2_offset + pixel_angles * self.parameter('wave2-period').get()) * self.parameter('wave2-amplitude').get())
        hues = self.pixel_distances * (self.parameter('radius-scale').get() + self._mixer.audio.getSmoothEnergy() * self.parameter('audio-radius-scale').get()) + wave1 + wave2

        audio_amplitude = self.parameter('audio-amplitude').get()
        fft = self._mixer.audio.getSmoothedFFT()
        if len(fft) > 0 and audio_amplitude:
            audio_pixel_angles = np.mod(pixel_angles / (math.pi * 2) + 1, 1)
            fft_size = len(fft)
            bin_per_pixel = np.int_(audio_pixel_angles * fft_size)
            wave_audio = audio_amplitude * np.asarray(fft)[bin_per_pixel]
            hues += wave_audio

        if self.parameter('audio-energy-lum-strength').get():
            lums = np.mod(np.int_(hues * self.parameter('audio-energy-lum-time').get()), self._luminance_steps)
            lums = self._mixer.audio.fader.color_cache.T[0][lums] * self.parameter('audio-energy-lum-strength').get()
        else:
            lums = hues

        luminance_indices = np.mod(np.abs(np.int_((self.luminance_offset + lums * luminance_scale) * self._luminance_steps)), self._luminance_steps)
        LS = self._fader.color_cache[luminance_indices].T
        luminances = LS[1]
        luminances += self._mixer.audio.getEnergy() * self.parameter('audio-brightness').get()

        hues = np.fmod(self.hue_inner + hues * self.parameter('hue-width').get(), 1.0)

        if self.parameter('audio-use-fader').get():
            #luminances *= self._mixer.audio.fader.color_cache.T[1][np.int_(luminance_indices * self.parameter('audio-fader-percent').get())] * self.parameter('audio-use-fader').get()
            #hues += self._mixer.audio.fader.color_cache.T[0][np.int_(hues * 255 * self.parameter('audio-fader-percent').get())] * self.parameter('audio-use-fader').get()
            hues += self._mixer.audio.fader.color_cache.T[0][np.int_(luminance_indices * self.parameter('audio-fader-percent').get())] * self.parameter('audio-use-fader').get()

        self.setAllHLS(hues, luminances, LS[2])
