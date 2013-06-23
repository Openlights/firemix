from noise import snoise3
import numpy as np

from lib.raw_preset import RawPreset
from lib.parameters import FloatParameter, IntParameter
import math
from lib.colors import clip

class SimplexNoise(RawPreset):
    """
    Simplex noise hue map
    """

    _luminance_steps = 256
    
    def setup(self):
        self.add_parameter(FloatParameter('hue-min', 0.0))
        self.add_parameter(FloatParameter('hue-max', 3.0))
        self.add_parameter(FloatParameter('speed', 0.7))
        self.add_parameter(FloatParameter('angle', 0.125))
        self.add_parameter(FloatParameter('color-speed', 0.2))
        self.add_parameter(IntParameter('resolution', 128))
        self.add_parameter(FloatParameter('scale', 0.25))
        self.add_parameter(FloatParameter('stretch', 1.0))
        self.add_parameter(FloatParameter('blackout', 0.25))
        self.add_parameter(FloatParameter('whiteout', 0.5))
        self.add_parameter(FloatParameter('luminance-scale', 0.75))
        self._offset_x = 0
        self._offset_y = 0
        self._offset_z = 0
        
        self.pixel_locations = np.asarray(self.scene().get_all_pixel_locations())

        self.color_lookup = {}
        self._setup_pars()

    def parameter_changed(self, parameter):
        self._setup_pars()

    def reset(self):
        self._setup_pars()

    def _setup_pars(self):
        self.hue_min = self.parameter('hue-min').get()
        self.hue_max = self.parameter('hue-max').get()
        self.color_speed = self.parameter('color-speed').get()
        self.scale = self.parameter('scale').get() / 100.0
        self.luminance_scale = self.parameter('luminance-scale').get() / 100.0

    def draw(self, dt):
        if self._mixer.is_onset():
            self._offset_z = -self._offset_z
            
        self._setup_pars()
        angle = self.parameter('angle').get()
        #self._offset_x += dt * self.parameter('speed').get() * math.cos(angle) * 2 * math.pi
        #self._offset_y += dt * self.parameter('speed').get() * math.sin(angle) * 2 * math.pi
        self._offset_x += dt * self.parameter('speed').get()
        self._offset_z += dt * self.parameter('color-speed').get()
        if self._mixer.is_onset():
            posterization = 2
        else:
            posterization = self.parameter('resolution').get()

        luminance_table = np.zeros(self._luminance_steps)
        luminance = 0.0
        for input in range(self._luminance_steps):
            if input > self.parameter('blackout').get() * self._luminance_steps:
                luminance -= 0.01
            elif input < self.parameter('whiteout').get() * self._luminance_steps:
                luminance += 0.01
            else:
                luminance = 0.5
            luminance = clip(0, luminance, 1.0)
            luminance_table[input] = math.floor(luminance * posterization) / posterization

        x, y = self.pixel_locations.T
        dx = x
        dy = y
        x = dx * math.cos(angle) - dy * math.sin(angle)
        y = dx * math.sin(angle) + dy * math.cos(angle)
        x *= self.parameter('stretch').get()
        x += self._offset_x
        y += self._offset_y
        locations = np.asarray([x,y]).T

        hues = np.asarray([snoise3(self.scale * location[0], \
                                   self.scale * location[1], \
                                   self._offset_z, 1, 0.5, 0.5) for location in locations])
        hues = (1.0 + hues) / 2
        hues = self.hue_min + ((np.int_(hues * posterization) / float(posterization)) * (self.hue_max - self.hue_min))
        brights = np.asarray([snoise3(self.luminance_scale * location[0], self.luminance_scale * location[1], self._offset_z, 1, 0.5, 0.5) for location in locations])
        brights = (1.0 + brights) / 2
        brights *= self._luminance_steps
        luminances = luminance_table[np.int_(brights)]

        self.setAllHLS(hues, luminances, 1.0)