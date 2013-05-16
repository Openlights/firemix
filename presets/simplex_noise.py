from lib.raw_preset import RawPreset
from lib.colors import hsv_float_to_rgb_uint8
from lib.parameters import FloatParameter

from ext import simplexnoise


class SimplexNoise(RawPreset):
    """
    Simplex noise hue map
    """

    def setup(self):
        self.add_parameter(FloatParameter('hue-min', 0.0))
        self.add_parameter(FloatParameter('hue-max', 1.0))
        self.add_parameter(FloatParameter('speed', 2.0))

        self.pixel_locations = self.scene().get_all_pixel_locations()
        self.scale = 0.01  # TODO: parameterize

        self._setup_pars()

    def parameter_changed(self, parameter):
        self._setup_pars()

    def _setup_pars(self):
        self.hue_min = self.parameter('hue-min').get()
        self.hue_max = self.parameter('hue-max').get()
        self.speed = 50.0 * self.parameter('speed').get()

    def draw(self, dt):
        speed = dt * self.speed
        d3 = self.scale * dt
        for pixel, location in self.pixel_locations:
            hue = (1.0 + simplexnoise.raw_noise_3d(self.scale * (location[0] + speed), self.scale * (location[1] + speed), d3)) / 2.0
            self.setp(pixel, hsv_float_to_rgb_uint8((hue, 1.0, 1.0)))
