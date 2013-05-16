from lib.raw_preset import RawPreset
from lib.colors import hsv_float_to_rgb_uint8
from lib.parameters import FloatParameter

from ext import simplexnoise


class NoiseGradient(RawPreset):
    """
    """

    def setup(self):
        self.add_parameter(FloatParameter('hue-min', 0.0))
        self.add_parameter(FloatParameter('hue-max', 1.0))
        self.add_parameter(FloatParameter('speed', 2.0))

        self.pixel_locations = self.scene().get_all_pixel_locations()

        self._setup_pars()

    def parameter_changed(self, parameter):
        self._setup_pars()

    def _setup_pars(self):
        self.hue_min = self.parameter('hue-min').get()
        self.hue_max = self.parameter('hue-max').get()
        self.speed = 50.0 * self.parameter('speed').get()

    def draw(self, dt):
        speed = dt * self.speed
        for pixel, location in self.pixel_locations:
            hue = simplexnoise.scaled_octave_noise_3d(1, 2.0, 0.01, self.hue_min, self.hue_max, location[0] + speed, location[1] + speed, dt)
            self.setp(pixel, hsv_float_to_rgb_uint8((hue, 1.0, 1.0)))