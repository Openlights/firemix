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
from lib.basic_tickers import fade, constant, speed, callback


class FixtureStepFade(Preset):
    """
    demonstrates the callback ticker by stepping through a list of fixtures
    and adding fade tickers for a new one every second
    """

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

    groups = [spikes, pentagon, star, spokes, outside]
    all_fixtures = [f for group in groups for f in group]
    idx = 0
    active_ticker = None
    constant_ticker = None

    def setup(self):
        self.constant_ticker = self.add_ticker(constant((), (0, 0, 0)), 0)
        self.active_ticker = self.add_ticker(speed(fade(self.all_fixtures[self.idx], Rainbow), 0.25), 1)
        self.add_ticker(callback(self.advance, 0.1), 1)

    def can_transition(self):
        return (self.idx == 0)

    def advance(self):
        if self.idx < len(self.all_fixtures) - 1:
            self.remove_ticker(self.constant_ticker)
            self.idx += 1
            self.remove_ticker(self.active_ticker)
            self.active_ticker = self.add_ticker(speed(fade(self.all_fixtures[self.idx], Rainbow), 0.25), 1)
        else:
            self.idx = 0
            self.remove_ticker(self.active_ticker)
            self.constant_ticker = self.add_ticker(constant((), (0, 0, 0)), 0)
            self.active_ticker = self.add_ticker(speed(fade(self.all_fixtures[self.idx], Rainbow), 0.25), 1)
