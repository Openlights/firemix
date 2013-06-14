import colorsys
import random
import math

from lib.raw_preset import RawPreset
from lib.parameters import FloatParameter, HLSParameter
from lib.color_fade import ColorFade
from lib.colors import clip

class SpiralGradient(RawPreset):
    """Spiral gradient that responds to onsets"""
       
    _fader = None
    _fader_resolution = 256
    
    def setup(self):
        self.add_parameter(FloatParameter('speed', 0.3))
        self.add_parameter(FloatParameter('hue-speed', 0.3))
        self.add_parameter(FloatParameter('angle-hue-width', 2.0))
        self.add_parameter(FloatParameter('radius-hue-width', 1.5))        
        self.add_parameter(FloatParameter('wave-hue-width', 0.1))        
        self.add_parameter(FloatParameter('wave-hue-period', 0.1))        
        self.add_parameter(FloatParameter('wave-speed', 0.1))        
        self.add_parameter(FloatParameter('hue-step', 0.1))    
        self.add_parameter(HLSParameter('color-start', (0.0, 0.5, 1.0)))
        self.add_parameter(HLSParameter('color-end', (1.0, 0.5, 1.0)))
        self.hue_inner = 0
        self.color_offset = 0
        self.wave_offset = random.random()

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
            self.pixel_angles[pixel] = (math.pi + math.atan2(dy, dx)) / (2.0 * math.pi)

        # Normalize
        max_distance = max(self.pixel_distances.values())
        for pixel in self.pixels:
            self.pixel_distances[pixel] /= max_distance
            
        self.parameter_changed(None)

    def parameter_changed(self, parameter):
        fade_colors = [self.parameter('color-start').get(), self.parameter('color-end').get(), self.parameter('color-start').get()]
   
        self._fader = ColorFade(fade_colors, self._fader_resolution)
    
    def reset(self):
        pass

    def draw(self, dt):
        if self._mixer.is_onset():
            self.hue_inner = self.hue_inner + self.parameter('hue-step').get()

        self.hue_inner += dt * self.parameter('hue-speed').get()
        self.wave_offset += dt * self.parameter('wave-speed').get()
        self.color_offset += dt * self.parameter('speed').get()

        wave_hue_period = 2 * math.pi * self.parameter('wave-hue-period').get()
        wave_hue_width = self.parameter('wave-hue-width').get()
        radius_hue_width = self.parameter('radius-hue-width').get()
        angle_hue_width = self.parameter('angle-hue-width').get()

        for pixel in self.pixels:
            angle = math.fmod(1.0 + self.pixel_angles[pixel] + math.sin(self.wave_offset + self.pixel_distances[pixel] * wave_hue_period) * wave_hue_width, 1.0)
            hue = self.color_offset + (radius_hue_width * self.pixel_distances[pixel]) + (2 * abs(angle - 0.5) * angle_hue_width)
            hue = math.fmod(math.floor(hue * self._fader_resolution) / self._fader_resolution, 1.0)
            color = self._fader.get_color(hue)
            self.setPixelHLS(pixel, (color[0] + self.hue_inner, color[1], color[2]))