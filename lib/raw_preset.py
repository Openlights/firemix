import numpy as np
import time
import logging
import colorsys

from lib.preset import Preset
from lib.buffer_utils import BufferUtils

log = logging.getLogger("firemix.lib.per_pixel_preset")


class RawPreset(Preset):
    """
    A RawPreset is a special type of Preset designed for per-pixel manipulation.
    It uses a single draw() method called every tick.
    """
    _pixel_buffer = None
    _indices = None
    _max_strand, _max_fixture, _max_pixel = (0, 0, 0)

    def __init__(self, mixer, name):
        Preset.__init__(self, mixer, name)
        self.init_pixels()

    def _reset(self):
        self.init_pixels()
        log.info("%s raw_preset _reset()" % self.__class__.__name__)
        Preset._reset(self)

    def init_pixels(self):
        """
        Sets up the pixel array
        """
        (self._max_strand, self._max_fixture, self._max_pixel) = self.scene().get_matrix_extents()
        self._pixel_buffer = BufferUtils.create_buffer()

    def draw(self, dt):
        """
        Override this method to define per-pixel behavior.
        Write output to self._pixel_buffer
        """
        pass

    def current_color(self, address):
        """
        Returns the current color of a pixel in RGB float
        address is a tuple of (strand, fixture, pixel)
        """
        return self._pixel_buffer[address]

    def setPixelHLS(self, index, color):
        self._pixel_buffer[index] = color
        
    def setPixelRGB(self, index, color):
        self.setPixelHLS(index, colorsys.rgb_to_hls(*color))
        
    def setPixelHSV(self, index, color):
        # There's probably a more efficient way to do this:
        hls = colorsys.rgb_to_hls(*colorsys.hsv_to_rgb(*color))

        self.setPixelHLS(index, hls)

    def setAllHLS(self, hues, luminances, saturations):
        """
        Sets the entire buffer, assuming an input list.
        """
        self._pixel_buffer[:,0] = hues
        self._pixel_buffer[:,1] = luminances
        self._pixel_buffer[:,2] = saturations
 
    def get_buffer(self):
        """
        Used by Mixer to render output
        """
        return self._pixel_buffer

    def tick(self, dt):
        """
        Unlike tick() in Preset, this method applies pixel_behavior to all pixels.
        """

        for parameter in self._parameters.values():
            parameter.tick(dt)
        
        self.draw(dt)

        self._ticks += 1

    def draw_to_buffer(self, buffer):
        return self.get_buffer()
