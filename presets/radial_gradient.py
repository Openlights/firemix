import colorsys
import random
import math
import numpy as np

from lib.raw_preset import RawPreset
from lib.colors import clip
from lib.parameters import FloatParameter

class RadialGradient(RawPreset):
    """Radial gradient that responds to onsets"""
    _luminance_steps = 256

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
        self.add_parameter(FloatParameter('blackout', 0.5))
        self.add_parameter(FloatParameter('whiteout', 0.1))
        self.add_parameter(FloatParameter('luminance-speed', 0.01))
        self.add_parameter(FloatParameter('luminance-scale', 1.0))
        self.hue_inner = random.random()
        self.wave1_offset = random.random()
        self.wave2_offset = random.random()
        self.luminance_offset = random.random()

        cx, cy = self.scene().center_point()

        self.locations = self.scene().get_all_pixel_locations()
        x,y = self.locations.T
        x -= cx
        y -= cy
        self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
        self.pixel_angles = math.pi + np.arctan2(y, x)
        self.pixel_distances /= max(self.pixel_distances)
        

    def reset(self):
        pass

    def draw(self, dt):
        if self._mixer.is_onset():
            self.hue_inner = math.fmod(self.hue_inner + self.parameter('hue-step').get(), 1.0)
            self.luminance_offset += self.parameter('hue-step').get()

        self.hue_inner += dt * self.parameter('speed').get()
        self.wave1_offset += self.parameter('wave1-speed').get() * dt
        self.wave2_offset += self.parameter('wave2-speed').get() * dt
        self.luminance_offset += self.parameter('luminance-speed').get() * dt

        luminance_table = []
        luminance = 0.0
        for input in range(self._luminance_steps):
            if input > self.parameter('blackout').get() * self._luminance_steps:
                luminance -= 0.01
                luminance = clip(0, luminance, 1.0)
            elif input < self.parameter('whiteout').get() * self._luminance_steps:
                luminance += 0.1
                luminance = clip(0, luminance, 1.0)
            else:
                luminance -= 0.01
                luminance = clip(0.5, luminance, 1.0)
            luminance_table.append(luminance)
        luminance_table = np.asarray(luminance_table)

        wave1_period = self.parameter('wave1-period').get()
        wave1_amplitude = self.parameter('wave1-amplitude').get()
        wave2_period = self.parameter('wave2-period').get()
        wave2_amplitude = self.parameter('wave2-amplitude').get()
        luminance_scale = self.parameter('luminance-scale').get()

        wave1 = np.abs(np.cos(self.wave1_offset + self.pixel_angles * wave1_period) * wave1_amplitude)
        wave2 = np.abs(np.cos(self.wave2_offset + self.pixel_angles * wave2_period) * wave2_amplitude)
        hues = self.pixel_distances + wave1 + wave2
        luminance_indices = np.mod(np.abs(np.int_((self.luminance_offset + hues * luminance_scale) * self._luminance_steps)), self._luminance_steps)
        luminances = luminance_table[luminance_indices]
        hues = np.fmod(self.hue_inner + hues * self.parameter('hue-width').get(), 1.0)

        self.setAllHLS(hues, luminances, 1.0)

        #colors = np.array([hues, luminances, 1.0]).T
        #self._pixel_buffer = colors
