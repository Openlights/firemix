from noise import snoise3

from lib.raw_preset import RawPreset
from lib.parameters import FloatParameter, IntParameter
import math

class SimplexNoise(RawPreset):
    """
    Simplex noise hue map
    """

    def setup(self):
        self.add_parameter(FloatParameter('hue-min', 0.0))
        self.add_parameter(FloatParameter('hue-max', 3.0))
        self.add_parameter(FloatParameter('speed', 0.7))
        self.add_parameter(FloatParameter('angle', 0.125))
        self.add_parameter(FloatParameter('color-speed', 0.2))
        self.add_parameter(IntParameter('resolution', 128))
        self.add_parameter(FloatParameter('scale', 0.25))
        self.add_parameter(FloatParameter('blackout', 0.25))
        self.add_parameter(FloatParameter('whiteout', 0.5))
        self.add_parameter(FloatParameter('luminance-scale', 0.75))
        self._offset_x = 0
        self._offset_y = 0
        self._offset_z = 0
        
        self.pixel_locations = self.scene().get_all_pixel_locations()
        self.pixel_addresses = {}

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
        self._offset_x += dt * self.parameter('speed').get() * math.cos(self.parameter('angle').get() * 2 * math.pi)
        self._offset_y += dt * self.parameter('speed').get() * math.sin(self.parameter('angle').get() * 2 * math.pi)
        self._offset_z += dt * self.parameter('color-speed').get()
        if self._mixer.is_onset():
            posterization = 2
        else:
            posterization = self.parameter('resolution').get()
        
        for pixel, location in self.pixel_locations:
            hue = (1.0 + snoise3(self.scale * location[0] + self._offset_x, self.scale * location[1] + self._offset_y, self._offset_z, 1, 0.5, 0.5)) / 2.0
            hue = self.hue_min + ((math.floor(hue * posterization) / posterization) * (self.hue_max - self.hue_min))
            
            brightness = (1.0 + snoise3(self.luminance_scale * location[0] + self._offset_x, self.luminance_scale * location[1] + self._offset_y, self._offset_z, 1, 0.5, 0.5)) / 2.0
            
            if brightness > self.parameter('whiteout').get():
                saturation = (brightness - self.parameter('whiteout').get()) / (1 - self.parameter('whiteout').get()) * 2
                if saturation > 1.0: saturation = 1.0
                saturation = math.floor(saturation * posterization) / posterization
                brightness = 1.0
            else:
                saturation = 1.0
            
            brightness = 0 if brightness < self.parameter('blackout').get() else 1.0
            
            self.setPixelHSV(pixel, (hue, saturation, brightness))