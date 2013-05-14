import numpy as np
import random

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
        self.vertices = self.vertices[:3]

        self.hues = {}
        self.pixels = self.scene().get_all_pixels()
        self.pixel_weights = {}

    def parameter_changed(self, parameter):
        pass

    def reset(self):
        random.seed()
        self._create_gradient()

    def draw(self, dt):
        for pixel in self.pixels:
            # 32 ms/frame
            hues, weights = zip(*[(self.hues[v], (1.0 / w)) for v, w in self.pixel_weights[pixel]])

            # 70 ms/frame
            hue = np.average(hues, weights=weights)
            color = hsv_float_to_rgb_uint8((hue, 1.0, 1.0))
            self.setp(pixel, color)

    def _create_gradient(self, threshold=550.0):
        # Pick a random hue at each vertex
        hmin = self.parameter('hue-min').get()
        hmax = self.parameter('hue-max').get()
        for v in self.vertices:
            self.hues[v] = random.uniform(hmin, hmax)

        for pixel in self.pixels:
            weights = []
            pixel_loc = self.scene().get_pixel_location(pixel)
            for vertex in self.vertices:
                dist = self.scene().get_point_distance(pixel_loc, vertex)
                if dist < 1.0:
                    dist = 1.0
                if dist < threshold:
                    weights.append((vertex, dist))
            self.pixel_weights[pixel] = weights
            print len(weights)
