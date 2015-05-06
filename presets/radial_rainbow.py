# This file is part of Firemix.
#
# Copyright 2013-2015 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

import math

from lib.preset import Preset
from lib.color_fade import Rainbow
from lib.basic_tickers import fade, offset, speed
from lib.parameters import FloatParameter


class RadialRainbow(Preset):
    """
    demonstrates scene attributes by assigning a color rainbow
    to fixtures based on their radial position in the scene
    """

    def setup(self):
        self.add_parameter(FloatParameter('speed', 0.2))
        self.add_parameter(FloatParameter('width', 1.0))
        self._create_tickers()

    def parameter_changed(self, parameter):
        if str(parameter) == 'width':
            self._create_tickers()

    def _create_tickers(self):
        self.clear_tickers()
        fixtures = self.scene().fixtures()
        midpoint_tuples = [(f.strand, f.address, f.midpoint()) for f in fixtures]
        extents = self.scene().extents()
        center = self.scene().center_point()
        for strand, address, midpoint in midpoint_tuples:
            dx, dy = (midpoint[0] - center[0], midpoint[1] - center[1])
            angle = (math.pi + math.atan2(dy, dx)) / (2.0 * math.pi) * self.parameter('width').get()
            self.add_ticker(speed(offset(fade((strand, address), Rainbow), angle), self.parameter('speed')))

