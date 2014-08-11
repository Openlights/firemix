import numpy as np
import colorsys
import random
import math

from lib.raw_preset import RawPreset
from lib.parameters import FloatParameter, HLSParameter
from lib.color_fade import ColorFade

class SpiralGradient(RawPreset):
    """Spiral gradient that responds to onsets"""
       
    _fader = None
    _fader_steps = 256
    
    def setup(self):
        self.add_parameter(FloatParameter('speed', 0.3))
        self.add_parameter(FloatParameter('hue-speed', 0.3))
        self.add_parameter(FloatParameter('angle-hue-width', 2.0))
        self.add_parameter(FloatParameter('radius-hue-width', 1.5))        
        self.add_parameter(FloatParameter('wave-hue-width', 0.1))        
        self.add_parameter(FloatParameter('wave-hue-period', 0.1))        
        self.add_parameter(FloatParameter('wave-speed', 0.1))        
        self.add_parameter(FloatParameter('onset-speed-boost', 5.0))
        self.add_parameter(FloatParameter('onset-speed-decay', 1.0))
        self.add_parameter(HLSParameter('color-start', (0.0, 0.5, 1.0)))
        self.add_parameter(HLSParameter('color-end', (1.0, 0.5, 1.0)))
        self.add_parameter(FloatParameter('center-distance', 0.0))
        self.add_parameter(FloatParameter('center-speed', 0.0))
        self.hue_inner = 0
        self.color_offset = 0
        self.wave_offset = random.random()

        self.center_offset_angle = 0

        self.onset_speed_boost = 1

        self.parameter_changed(None)

    def parameter_changed(self, parameter):
        fade_colors = [self.parameter('color-start').get(), self.parameter('color-end').get(), self.parameter('color-start').get()]

        self._fader = ColorFade(fade_colors, self._fader_steps)

    def reset(self):
        self.locations = self.scene().get_all_pixel_locations()

    def draw(self, dt):
        if self._mixer.is_onset():
            self.onset_speed_boost = self.parameter('onset-speed-boost').get()

        self.center_offset_angle += dt * self.parameter('center-speed').get() * self.onset_speed_boost
        self.hue_inner += dt * self.parameter('hue-speed').get() * self.onset_speed_boost
        self.wave_offset += dt * self.parameter('wave-speed').get() * self.onset_speed_boost
        self.color_offset += dt * self.parameter('speed').get() * self.onset_speed_boost

        self.onset_speed_boost = max(1, self.onset_speed_boost - self.parameter('onset-speed-decay').get())

        wave_hue_period = 2 * math.pi * self.parameter('wave-hue-period').get()
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

        angles = np.mod(1.0 + self.pixel_angles + np.sin(self.wave_offset + self.pixel_distances * wave_hue_period) * wave_hue_width, 1.0)
        hues = self.color_offset + (radius_hue_width * self.pixel_distances) + (2 * np.abs(angles - 0.5) * angle_hue_width)
        hues = np.int_(np.mod(hues, 1.0) * self._fader_steps)
        colors = self._fader.color_cache[hues]
        colors = colors.T
        colors[0] = np.mod(colors[0] + self.hue_inner, 1.0)
        colors = colors.T

        self._pixel_buffer = colors