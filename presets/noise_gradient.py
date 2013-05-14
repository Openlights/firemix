import colorsys
import random

from lib.raw_preset import RawPreset
from lib.colors import float_to_uint8
from lib.parameters import FloatParameter


class NoiseGradient(RawPreset):
    """
    """

    def setup(self):
        self.add_parameter(FloatParameter('hue-min', 0.0))
        self.add_parameter(FloatParameter('hue-max', 1.0))
        self.add_parameter(FloatParameter('speed', 1.0))
        self.add_parameter(FloatParameter('width', 0.5))

        self._vertices = self.scene().get_intersection_points()
        self._hues = {}
        self._pixels = self.scene().get_all_pixels()

    def parameter_changed(self, parameter):
        pass

    def reset(self):
        random.seed()
        self._create_gradient()

    def draw(self, dt):
        for pixel in self._pixels:
            for vertex in self._vertices:
                if self.scene().get_point_distance(self.scene().get_pixel_location(pixel), vertex) < 10:
                    self.setp(pixel, (255, 0, 0))

    def _create_gradient(self):
        for v in self._vertices:
            self._hues[v] = random.random()

        # Todo: Need to precalculate a list of (weight, vertex) for each pixel!
