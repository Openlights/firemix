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


from builtins import str
import numpy as np
import os
import logging
import colorsys

from lib.json_dict import JSONDict
from lib.buffer_utils import BufferUtils
from lib.parameters import BoolParameter
from lib.util import slugify

log = logging.getLogger("firemix.lib.pattern")


class Pattern(JSONDict):
    """Base Pattern.  Does nothing."""

    def __init__(self, app, slug=""):
        self._app = app
        self._ticks = 0
        self._elapsed_time = 0
        self._parameters = {}
        self._watches = {}
        self._instance_name = ""
        self._instance_slug = slug
        self.initialized = False
        self.disabled = False

        filepath = os.path.join(os.getcwd(), "data", "presets", "".join([slug, ".json"]))
        JSONDict.__init__(self, 'preset', filepath, True)

        self.open()

    def open(self):
        try:
            self.load(False)
        except ValueError:
            print("Error loading %s" % self.filename)
            return False

        self._instance_name = self.data.get('name', "")

        self.add_parameter(BoolParameter('allow-playback', True))
        self.setup()
        self._reset()
        self.load_params_from_json(self.data.get('params', {}))
        self.parameter_changed(None)
        self.initialized = True

    def save(self):
        self.data["name"] = self._instance_name
        self.data["classname"] = self.__class__.__name__
        self.data["file-version"] = 1
        self.data["params"] = {}
        for n, p in self._parameters.items():
            self.data["params"][n] = p.get_as_str()
        JSONDict.save(self)

    def __repr__(self):
        return "%s (%s)" % (self._instance_name, self.__class__.__name__)

    def set_name(self, name):
        self._instance_name = name
        self._instance_slug = slugify(name)
        self.filename = os.path.join(os.getcwd(), "data", "presets",
                                     "".join([self._instance_slug, ".json"]))
        self.save()

    def name(self):
        return self._instance_name

    def slug(self):
        return self._instance_slug

    def reset(self):
        """
        Override this method to perform any initialization that will be triggered
        each time the preset is about to start playing.  Note that code that should
        only run once (e.g. creating parameters) should go in the setup() method instead.
        """
        pass

    def _reset(self):
        self.reset()

    def setup(self):
        """
        Extend this method to initialize your pattern.
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

    def load_params_from_json(self, json_data):
        for k, v in json_data.items():
            try:
                self.parameter(k).set_from_str(str(v))
            except AttributeError:
                log.warn("Parameter %s found in JSON data but not found in preset class.  Perhaps it was renamed?" % k)

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

        for parameter in list(self._parameters.values()):
            parameter.tick(dt)

        self._ticks += 1

    def render(self, out):
        raise NotImplementedError

    def tick_rate(self):
        # TODO: should have a different way of getting to the mixer settings
        return self._app.mixer.get_tick_rate()

    def _convert_color(self, color):
        if (type(color[0]) == float) or (type(color[1]) == float) or (type(color[2]) == float) or (type(color[1]) ==np.float32):
            return tuple([int(c*255) for c in color])
        else:
            return color

    def scene(self):
        # TODO: this api is bogus
        return self._app.mixer.scene()

    def setPixelHLS(self, buf, index, color):
        buf[index] = color

    def setPixelRGB(self, buf, index, color):
        self.setPixelHLS(buf, index, colorsys.rgb_to_hls(*color))

    def setPixelHSV(self, buf, index, color):
        # There's probably a more efficient way to do this:
        hls = colorsys.rgb_to_hls(*colorsys.hsv_to_rgb(*color))

        self.setPixelHLS(buf, index, hls)

    def setAllHLS(self, buf, hues, lightnesses, saturations):
        """
        Sets the entire buffer, assuming an input list.
        """
        buf['hue'] = hues
        buf['light'] = lightnesses
        buf['sat'] = saturations

    def clear(self, buf):
        buf.fill(0)
