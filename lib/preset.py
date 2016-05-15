# This file is part of Firemix.
#
# Copyright 2013-2016 Jonathan Evans <jon@craftyjon.com>
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

from lib.buffer_utils import BufferUtils
from lib.parameters import BoolParameter

log = logging.getLogger("firemix.lib.preset")


class Preset:
    """Base Preset.  Does nothing."""

    def __init__(self, mixer, name=""):
        self._mixer = mixer
        self._ticks = 0
        self._elapsed_time = 0
        self._parameters = {}
        self._watches = {}

        self._instance_name = name
        self.initialized = False
        self.disabled = False
        self.add_parameter(BoolParameter('allow-playback', True))
        self.init_pixels()
        self.setup()

    def __repr__(self):
        return "%s (%s)" % (self._instance_name, self.__class__.__name__)

    def set_name(self, name):
        self._instance_name = name

    def name(self):
        return self._instance_name

    def reset(self):
        """
        Override this method to perform any initialization that will be triggered
        each time the preset is about to start playing.  Note that code that should
        only run once (e.g. creating parameters) should go in the setup() method instead.
        """
        pass

    def _reset(self):
        self.init_pixels()
        self.reset()

    def init_pixels(self):
        """
        Sets up the pixel array
        """
        self._pixel_buffer = BufferUtils.create_buffer()

    def setup(self):
        """
        Override this method to initialize your tickers.
        """
        pass

    def parameter_changed(self, parameter):
        """
        This callback will be called when any parameters are updated.
        """
        pass

    def can_transition(self):
        """
        Override this method to define clear points at which the mixer can
        transition to or from the preset.  By default, the mixer can
        transition at any time.
        """
        return True

    def add_parameter(self, parameter):
        """
        Adds a parameter to the preset (see ./lib/parameters.py)
        """
        parameter.set_parent(self)
        self._parameters[str(parameter)] = parameter

    def get_parameters(self):
        return self._parameters

    def clear_parameters(self):
        self._parameters = []

    def parameter(self, key):
        return self._parameters.get(key, None)

    def set_parameter(self, key, value):
        """
        Attempts to change the value of a parameter. Returns False if the parameter does not
        exist or the new value is invalid.
        """
        try:
            self._parameters[key].set(value)
            return True
        except KeyError:
            return False

    def add_watch(self, watch):
        self._watches[str(watch)] = watch

    def get_watches(self):
        return self._watches

    def clear_watches(self):
        self._watches = []

    def watch(self, key):
        return self._watches.get(key, None)

    def tick(self, dt):  
        if self.disabled:
            return

        for parameter in self._parameters.values():
            parameter.tick(dt)
        
        self.draw(dt)

        self._ticks += 1

    def tick_rate(self):
        # TODO: should have a different way of getting to the mixer settings
        return self._mixer.get_tick_rate()

    def _convert_color(self, color):
        if (type(color[0]) == float) or (type(color[1]) == float) or (type(color[2]) == float) or (type(color[1]) ==np.float32):
            return tuple([int(c*255) for c in color])
        else:
            return color

    def scene(self):
        return self._mixer.scene()

    def get_buffer(self):
        """
        Used by Mixer to render output
        """
        return self._pixel_buffer

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
