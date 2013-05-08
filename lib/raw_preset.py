import numpy as np
import time
import logging

from lib.preset import Preset
from lib.commands import SetPixel

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
        Preset._reset(self)

    def init_pixels(self):
        """
        Sets up the pixel array
        """
        (self._max_strand, self._max_fixture, self._max_pixel) = self.scene().get_matrix_extents()
        self._pixel_buffer = np.zeros((self._max_strand, self._max_fixture, self._max_pixel, 3), dtype=np.float32)

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

    def get_buffer(self):
        """
        Used by Mixer to render output
        """
        return self._pixel_buffer

    def tick(self):
        """
        Unlike tick() in Preset, this method applies pixel_behavior to all pixels.
        """
        if self._mixer._enable_profiling:
            start = time.time()

        dt = self._ticks * (1.0 / self.tick_rate())
        self.draw(dt)

        self._ticks += 1

        if self._mixer._enable_profiling:
            tick_time = 1000.0 * (time.time() - start)
            if tick_time > 30.0:
                log.warn("%s slow frame: %d ms" % (self.__class__, tick_time))
