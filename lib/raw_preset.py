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
        self._pixel_buffer = BufferUtils.create_buffer(self._mixer._app)

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

    def setPixelHLS(self, location, color):
        x, y = BufferUtils.get_buffer_address(self._mixer._app, location)
        self._pixel_buffer[x][y] = color
        
    def setPixelRGB(self, location, color):
        self.setPixelHLS(location, colorsys.rgb_to_hls(*color))
        
    def setPixelHSV(self, location, color):
        # colorsys doesn't have hsv to hls direct, so here it is:
        #L = (2 - color[1]) * color[2]
        #S = color[1] * color[2]
        #S /= L  if (L <= 1) else 2 - L
        #L /= 2

        # Hack cause I'm lazy at the moment
        hls = colorsys.rgb_to_hls(*colorsys.hsv_to_rgb(*color))

        self.setPixelHLS(location, hls)
 
    def get_buffer(self):
        """
        Used by Mixer to render output
        """
        return self._pixel_buffer

    def tick(self, dt):
        """
        Unlike tick() in Preset, this method applies pixel_behavior to all pixels.
        """
        # if self._mixer._enable_profiling:
        #     start = time.time()

        # TODO: This does not account for varying frame rate
        current_time = self._ticks * dt

        for parameter in self._parameters.values():
            parameter.tick(dt)
        
        self.draw(current_time)

        self._ticks += 1

        # if self._mixer._enable_profiling:
        #     tick_time = 1000.0 * (time.time() - start)
        #     if tick_time > 30.0:
        #         log.info("%s slow frame: %d ms" % (self.__class__, tick_time))
