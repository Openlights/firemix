import colorsys
import random
import math

from lib.raw_preset import RawPreset
from lib.parameters import FloatParameter, HLSParameter, IntParameter
from lib.color_fade import ColorFade

class StripeGradient(RawPreset):
    _fader = None
    
    def setup(self):
        self.add_parameter(FloatParameter('speed', 0.01))
        self.add_parameter(FloatParameter('angle-speed', 0.1))
        self.add_parameter(FloatParameter('stripe-width', 20))
        self.add_parameter(FloatParameter('center-orbit-distance', 200))
        self.add_parameter(FloatParameter('center-orbit-speed', 0.1))
        self.add_parameter(FloatParameter('hue-step', 0.1))
        self.add_parameter(IntParameter('posterization', 8))
        self.add_parameter(HLSParameter('color-start', (0.0, 0.0, 1.0)))
        self.add_parameter(HLSParameter('color-end', (1.0, 1.0, 1.0)))
        self.hue_inner = random.random() + 100
        self._center_rotation = random.random()
        self.stripe_angle = random.random()

        self.pixels = self.scene().get_all_pixels_logical()
        cx, cy = self.scene().center_point()

        # Find radius to each pixel
        self.pixel_distances = {}
        self.pixel_angles = {}
        for pixel in self.pixels:
            x, y = self.scene().get_pixel_location(pixel)
            dx = x - cx
            dy = y - cy
            d = math.sqrt(math.pow(dx, 2) + math.pow(dy, 2))
            self.pixel_distances[pixel] = d
            self.pixel_angles[pixel] = (math.pi + math.atan2(dy, dx)) / (2.0 * math.pi)

        # Normalize
        max_distance = max(self.pixel_distances.values())
        for pixel in self.pixels:
            self.pixel_distances[pixel] /= max_distance
            
        self.parameter_changed(None)

    def parameter_changed(self, parameter):
        fade_colors = [self.parameter('color-start').get(), self.parameter('color-start').get(), self.parameter('color-end').get(), self.parameter('color-end').get(), self.parameter('color-start').get()]
#        fade_colors = [self.parameter('color-start').get(), self.parameter('color-end').get(), self.parameter('color-start').get()]
#        fade_colors = [self.parameter('color-start').get(), self.parameter('color-end').get(), self.parameter('color-start').get()]
   
        self._fader = ColorFade(fade_colors, self.parameter('posterization').get())
    
    def reset(self):
        pass

    def draw(self, dt):
        if self._mixer.is_onset():
            self.hue_inner = self.hue_inner + self.parameter('hue-step').get()

        self.hue_inner += dt * self.parameter('speed').get()
        self._center_rotation += dt * self.parameter('center-orbit-speed').get()
        self.stripe_angle += dt * self.parameter('angle-speed').get()
        stripe_width = self.parameter('stripe-width').get()
        cx, cy = self.scene().center_point()
        cx += math.cos(self._center_rotation) * self.parameter('center-orbit-distance').get()
        cy += math.sin(self._center_rotation) * self.parameter('center-orbit-distance').get()

        posterization = self.parameter('posterization').get()
        for pixel in self.pixels:
            x, y = self.scene().get_pixel_location(pixel)
            dx = x - cx
            dy = y - cy
            x = dx * math.cos(self.stripe_angle) - dy * math.sin(self.stripe_angle)
            y = dx * math.sin(self.stripe_angle) + dy * math.cos(self.stripe_angle)
            x = (x / stripe_width) % 1.0
            y = (y / stripe_width) % 1.0
            x = abs(x - 0.5)
            y = abs(y - 0.5)
            hue = (x+y) * posterization
            color1 = self._fader.get_color(hue)
            self.setPixelHLS(pixel, ((color1[0] + self.hue_inner) % 1.0, color1[1], color1[2]))