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

        self.pixels = self.scene().get_all_pixels()
        cx, cy = self.scene().center_point()

        self.locations = np.asarray(self.scene().get_all_pixel_locations())
        x,y = self.locations.T
        x -= cx
        y -= cy
        self.pixel_distances = np.sqrt(np.square(x) + np.square(y))
        self.pixel_angles = np.arctan2(y, x) / (2.0 * math.pi)
        self.pixel_distances /= max(self.pixel_distances)

        self.parameter_changed(None)
        

    def reset(self):
        pass

    def parameter_changed(self, p):
        self._hue_step = self.parameter('hue-step').get()
        self._speed = self.parameter('speed').get()
        self._wave1_speed = self.parameter('wave1-speed').get()
        self._wave2_speed = self.parameter('wave2-speed').get()
        self._luminance_speed = self.parameter('luminance-speed').get()
        self._blackout = self.parameter('blackout').get()
        self._whiteout = self.parameter('whiteout').get()
        self._wave1_period = self.parameter('wave1-period').get()
        self._wave1_amplitude = self.parameter('wave1-amplitude').get()
        self._wave2_period = self.parameter('wave2-period').get()
        self._wave2_amplitude = self.parameter('wave2-amplitude').get()
        self._luminance_scale = self.parameter('luminance-scale').get()

    def draw(self, dt):
        if self._mixer.is_onset():
            self.hue_inner = math.fmod(self.hue_inner + self._hue_step, 1.0)
            self.luminance_offset += self._hue_step

        self.hue_inner += dt * self._speed
        self.wave1_offset += self._wave1_speed * dt
        self.wave2_offset += self._wave2_speed * dt
        self.luminance_offset += self._luminance_speed * dt

        luminance_table = []
        luminance = 0.0
        for input in range(self._luminance_steps):
            if input > self._blackout * self._luminance_steps:
                luminance -= 0.01
                luminance = clip(0, luminance, 1.0)
            elif input < self._whiteout * self._luminance_steps:
                luminance += 0.1
                luminance = clip(0, luminance, 1.0)
            else:
                luminance -= 0.01
                luminance = clip(0.5, luminance, 1.0)
            luminance_table.append(luminance)
        luminance_table = np.asarray(luminance_table)



        wave1 = np.abs(np.cos(self.wave1_offset + self.pixel_angles * self._wave1_period) * self._wave1_amplitude)
        wave2 = np.abs(np.cos(self.wave2_offset + self.pixel_angles * self._wave2_period) * self._wave2_amplitude)
        hues = self.pixel_distances + wave1 + wave2
        luminance_indices = np.mod(np.abs(np.int_((self.luminance_offset + hues * self._luminance_scale) * self._luminance_steps)), self._luminance_steps)
        luminances = luminance_table[luminance_indices]
        hues = np.fmod(self.hue_inner + hues * self.parameter('hue-width').get(), 1.0)

        self.setAllHLS(hues, luminances, 1.0)

        #for i in range(len(self.pixels)):
        #    self.setPixelHLS(self.pixels[i], (hues[i], luminances[i], 1.0))
