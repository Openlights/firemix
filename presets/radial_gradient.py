import colorsys
import random
import math

from lib.raw_preset import RawPreset
from lib.colors import hsv_float_to_rgb_uint8
from lib.parameters import FloatParameter

class RadialGradient(RawPreset):
    """Radial gradient that responds to onsets"""

    def setup(self):
        self.add_parameter(FloatParameter('speed', 0.25))
        self.add_parameter(FloatParameter('hue_width', 2.0))
        self.add_parameter(FloatParameter('hue_step', 0.1))    
        self.hue_inner = random.random()

        self.pixels = self.scene().get_all_pixels()
        cx, cy = self.scene().get_centroid()

        # Find radius to each pixel
        self.pixel_distances = {}
        for pixel in self.pixels:
            x, y = self.scene().get_pixel_location(pixel)
            dx = abs(x - cx)
            dy = abs(y - cy)
            d = math.sqrt(math.pow(dx, 2) + math.pow(dy, 2))
            self.pixel_distances[pixel] = d

        # Normalize
        max_distance = max(self.pixel_distances.values())
        for pixel in self.pixels:
            self.pixel_distances[pixel] /= max_distance

    def reset(self):
        pass

    def draw(self, dt):
        if self._mixer.is_onset():
            self.hue_inner = math.fmod(self.hue_inner + self.parameter('hue_step').get(), 1.0)

        start = math.fmod(self.hue_inner + (dt * self.parameter('speed').get()), 1.0)

        for pixel in self.pixels:
            hue = start + (self.parameter('hue_width').get() * self.pixel_distances[pixel])
            self.setp(pixel, hsv_float_to_rgb_uint8((hue, 1.0, 1.0)))