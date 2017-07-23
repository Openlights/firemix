from __future__ import division
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

from builtins import object
from past.utils import old_div
import unittest


class Fixture(object):
    """
    Basic model for a 1D linear fixture
    """

    def __init__(self, data=None):
        self._data = data
        self.strand = data.get("strand", 0)
        self.address = data.get("address", 0)
        self.pixels = data.get("pixels", 0)
        self.pos1 = tuple(data.get("pos1", (0, 0)))
        self.pos2 = tuple(data.get("pos2", (0, 0)))

    def __repr__(self):
        return "Fixture%d [%d:%d]" % (self.pixels, self.strand, self.address)

    def midpoint(self):
        """
        Returns the (x, y) of the midpoint of the fixture
        """
        p1 = self.pos1
        p2 = self.pos2
        return (old_div((p1[0] + p2[0]), 2), old_div((p1[1] + p2[1]), 2))

    def pixel_neighbors(self, pixel):
        """
        Returns the one or two neighbors of a pixel on a fixture.
        """
        if pixel < 0 or pixel >= self.pixels:
            return []
        elif pixel == 0:
            return [1]
        elif pixel == (self.pixels - 1):
            return [self.pixels - 2]
        else:
            return [pixel - 1, pixel + 1]
