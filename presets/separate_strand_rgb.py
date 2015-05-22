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

from lib.preset import Preset
from lib.color_fade import Rainbow
from lib.basic_tickers import fade, offset, speed
from lib.parameters import FloatParameter


class SeparateStrandRGB(Preset):
    outside = [(0, 0),
               (1, 0),
               (1, 3),
               (1, 4),
               (3, 0),
               (3, 4),
               (5, 0),
               (5, 1),
               (5, 2),
               (0, 3)]

    spokes = [(0, 2),
              (1, 2),
              (2, 0),
              (4, 0),
              (5, 4)]

    star = [(0, 1),
            (1, 1),
            (2, 2),
            (2, 1),
            (3, 1),
            (3, 3),
            (4, 1),
            (4, 2),
            (5, 3),
            (0, 4)]

    pentagon = [(6, 0),
                (2, 3),
                (3, 2),
                (4, 3),
                (6, 3)]

    spikes = [(6, 2),
              (6, 1),
              (2, 4),
              (4, 4),
              (6, 4)]

    def setup(self):
        self.add_parameter(FloatParameter('speed', 0.5))
        self.add_parameter(FloatParameter('interval', 0.05))
        self._setup_tickers()

    def parameter_changed(self, parameter):
        self._setup_tickers()

    def _setup_tickers(self):
        self.clear_tickers()
        self.add_ticker(speed(fade(self.outside, Rainbow), self.parameter('speed')))
        self.add_ticker(speed(offset(fade(self.spokes, Rainbow), 1.0 * self.parameter('interval').get()), self.parameter('speed').get()))
        self.add_ticker(speed(offset(fade(self.star, Rainbow), 2.0 * self.parameter('interval').get()), self.parameter('speed').get()))
        self.add_ticker(speed(offset(fade(self.pentagon, Rainbow), 3.0 * self.parameter('interval').get()), self.parameter('speed').get()))
        self.add_ticker(speed(offset(fade(self.spikes, Rainbow), 4.0 * self.parameter('interval').get()), self.parameter('speed').get()))