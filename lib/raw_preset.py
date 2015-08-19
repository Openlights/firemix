# This file is part of Firemix.
#
# Copyright 2013-2015 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Firemix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Firemix.  If not, see <http://www.gnu.org/licenses/>.

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
        if self.disabled:
            return

        for parameter in self._parameters.values():
            parameter.tick(dt)
        
        self.draw(dt)

        self._ticks += 1

    def draw_to_buffer(self, buffer):
        return self.get_buffer()
