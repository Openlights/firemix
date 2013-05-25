import noise
from noise import snoise3

from lib.raw_preset import RawPreset
from lib.parameters import FloatParameter, IntParameter
from lib.buffer_utils import BufferUtils
from lib.colors import hsv_float_to_rgb_uint8


class SimplexNoise(RawPreset):
    """
    Simplex noise hue map
    """

    def setup(self):
        self.add_parameter(FloatParameter('hue-min', 0.0))
        self.add_parameter(FloatParameter('hue-max', 1.0))
        self.add_parameter(FloatParameter('speed', 7.0))
        self.add_parameter(FloatParameter('color-speed', 0.5))
        self.add_parameter(IntParameter('resolution', 128))

        self.pixel_locations = self.scene().get_all_pixel_locations()
        self.pixel_addresses = {}
        self.scale = 0.01  # TODO: parameterize

        self.color_lookup = {}
        self._setup_pars()

    def parameter_changed(self, parameter):
        self._setup_pars()

    def _setup_pars(self):
        self.hue_min = self.parameter('hue-min').get()
        self.hue_max = self.parameter('hue-max').get()
        self.speed = 10.0 * self.parameter('speed').get()
        self.color_speed = self.parameter('color-speed').get()

        res = self.parameter('resolution').get()
        for i in range(res):
            hue = self.hue_min + ((float(i) / res) * (self.hue_max - self.hue_min))
            self.color_lookup[i] = hsv_float_to_rgb_uint8((hue, 1.0, 1.0))

    def draw(self, dt):
        delta = dt * self.speed
        d3 = self.color_speed * dt
        res = self.parameter('resolution').get()
        setp = self.setp

        for pixel, location in self.pixel_locations:
            hue = (1.0 + snoise3(self.scale * (location[0] + delta), self.scale * (location[1] + delta), d3, 1, 0.5, 0.5)) / 2.0
            setp(pixel, self.color_lookup[int(hue * res)])
