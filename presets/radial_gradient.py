import colorsys
import random
import math

from lib.raw_preset import RawPreset
from lib.colors import hsv_float_to_rgb_uint8
from lib.parameters import FloatParameter

class RadialGradient(RawPreset):
    """Radial gradient that responds to onsets"""

    def setup(self):
        self.add_parameter(FloatParameter('speed', 0.1))
        self.add_parameter(FloatParameter('hue-width', 1.5))
        self.add_parameter(FloatParameter('hue-step', 0.1))    
        self.add_parameter(FloatParameter('wave1-amplitude', 0.5))
        self.add_parameter(FloatParameter('wave1-period', 1.5))
        self.add_parameter(FloatParameter('wave1-speed', 0.05))
        self.add_parameter(FloatParameter('wave2-amplitude', 0.5))
        self.add_parameter(FloatParameter('wave2-period', 1.5))
        self.add_parameter(FloatParameter('wave2-speed', 0.1))
        self.add_parameter(FloatParameter('blackout', 0.5))
        self.add_parameter(FloatParameter('whiteout', 0.1))
        self.add_parameter(FloatParameter('luminance-speed', 0.01))
        self.add_parameter(FloatParameter('luminance-scale', 1.0))
        self.hue_inner = random.random()
        self.wave1_offset = random.random()
        self.wave2_offset = random.random()
        self.luminance_offset = random.random()

        self.pixels = self.scene().get_all_pixels()
        cx, cy = self.scene().get_centroid()

        # Find radius to each pixel
        self.pixel_distances = {}
        self.pixel_angles = {}
        for pixel in self.pixels:
            x, y = self.scene().get_pixel_location(pixel)
            dx = x - cx
            dy = y - cy
            d = math.sqrt(math.pow(dx, 2) + math.pow(dy, 2))
            self.pixel_distances[pixel] = d
            self.pixel_angles[pixel] = (math.pi + math.atan2(dy, dx))

        # Normalize
        max_distance = max(self.pixel_distances.values())
        for pixel in self.pixels:
            self.pixel_distances[pixel] /= max_distance

    def reset(self):
        pass

    def draw(self, dt):
        if self._mixer.is_onset():
            self.hue_inner = math.fmod(self.hue_inner + self.parameter('hue-step').get(), 1.0)
            self.luminance_offset += self.parameter('hue-step').get()

        start = self.hue_inner + (dt * self.parameter('speed').get())
        self.wave1_offset += self.parameter('wave1-speed').get()
        self.wave2_offset += self.parameter('wave2-speed').get()
        self.luminance_offset += self.parameter('luminance-speed').get()
        
        for pixel in self.pixels:
            wave1 = abs(math.cos(self.wave1_offset + self.pixel_angles[pixel] * self.parameter('wave1-period').get()) * self.parameter('wave1-amplitude').get())
            wave2 = abs(math.cos(self.wave2_offset + self.pixel_angles[pixel] * self.parameter('wave2-period').get()) * self.parameter('wave2-amplitude').get())
            hue = self.pixel_distances[pixel] + wave1 + wave2
            luminance = abs(math.fmod(self.luminance_offset + hue * self.parameter('luminance-scale').get(), 1.0))
            hue = math.fmod(start + hue * self.parameter('hue-width').get(), 1.0)
            brightness = 0 if luminance > self.parameter('blackout').get() else 1.0
            saturation = 0 if luminance < self.parameter('whiteout').get() else 1.0
            self.setPixelHSV(pixel, (hue, saturation, brightness))