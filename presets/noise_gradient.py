import random
import math

from lib.raw_preset import RawPreset
from lib.colors import hsv_float_to_rgb_uint8
from lib.parameters import FloatParameter


class NoiseGradient(RawPreset):
    """
    """

    def setup(self):
        self.add_parameter(FloatParameter('hue-min', 0.0))
        self.add_parameter(FloatParameter('hue-max', 1.0))
        self.add_parameter(FloatParameter('speed', 1.0))
        self.add_parameter(FloatParameter('width', 0.5))

        self.vertices = self.scene().get_intersection_points()
        random.shuffle(self.vertices)
        self.vertices = self.vertices[:10]

        self.hues = {}
        self.colors = {}
        self.pixels = self.scene().get_all_pixels()
        self.pixel_weights = {}
        self.pixel_hues = {}

        self.delta = 0.01

    def parameter_changed(self, parameter):
        pass

    def reset(self):
        random.seed()
        self._create_gradient()

    def draw(self, dt):
        for pixel in self.pixels:
            colors, weights = zip(*[(self.hues[v], w) for v, w in self.pixel_weights[pixel]])
            color = hsv_float_to_rgb_uint8((self._weighted_average(colors, weights), 1.0, 1.0))
            self.setp(pixel, color)

        for vertex in self.hues:
            self.hues[vertex] = math.fmod(self.hues[vertex] + self.delta, 1.0)

    def _create_gradient(self, relax=5.0, threshold=250.0):
        # Pick a random hue at each vertex
        hmin = self.parameter('hue-min').get()
        hmax = self.parameter('hue-max').get()
        for v in self.vertices:
            self.hues[v] = random.uniform(hmin, hmax)
            self.colors[v] = hsv_float_to_rgb_uint8((self.hues[v], 1.0, 1.0))

        for pixel in self.pixels:
            weights = []
            pixel_loc = self.scene().get_pixel_location(pixel)
            for vertex in self.vertices:
                dist = self.scene().get_point_distance(pixel_loc, vertex)
                if dist < 1.0:
                    dist = 1.0
                if dist < threshold:
                    weights.append((vertex, 1.0 / dist))
            self.pixel_weights[pixel] = weights

    def _weighted_average_color(self, colors, weights):
        n = [(int(c[0] * w), int(c[1] * w), int(c[2] * w)) for c, w in zip(colors, weights)]
        n = [sum(x) for x in zip(*n)]
        d = sum(weights)
        if d == 0:
            return 0.0
        return tuple([int(float(x) / d) for x in n])

    def _weighted_average(self, data, weights):
        n = sum([x * w for x, w in zip(data, weights)])
        d = sum(weights)
        if d == 0:
            return 0.0
        return float(n) / d