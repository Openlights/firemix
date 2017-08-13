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

from builtins import range
import numpy as np

from lib.transition import Transition
from lib.buffer_utils import BufferUtils, struct_flat


class FixtureStrobe(Transition):
    """
    """

    def __init__(self, app):
        Transition.__init__(self, app)
        self._strobing = []
        self._time = {}
        self._on = {}
        self._duration = 0.1

    def __str__(self):
        return "Fixture Strobe"

    def reset(self):
        self.fixtures = self._app.scene.fixtures()
        buffer_size = BufferUtils.get_buffer_size()
        self.mask = np.tile(False, buffer_size)

        np.random.seed()
        self.rand_index = np.arange(len(self.fixtures))
        np.random.shuffle(self.rand_index)

        self.last_idx = 0

    def render(self, start, end, progress, out):
        start[self.mask] = (0.0, 0.0, 0.0)
        end[np.invert(self.mask)] = (0.0, 0.0, 0.0)

        idx = int(progress * len(self.rand_index))

        if idx >= self.last_idx:
            for i in range(self.last_idx, idx):
                fix = self.fixtures[self.rand_index[i]]
                self._strobing.append(fix)
                self._time[fix] = progress
                self._on[fix] = True
        else:
            for i in range(idx, self.last_idx):
                fix = self.fixtures[self.rand_index[i]]
                if fix in self._strobing:
                    self._strobing.remove(fix)
                pix_start, pix_end = BufferUtils.get_fixture_extents(fix.strand, fix.address)
                self.mask[pix_start:pix_end] = False
                self._on[fix] = False
        self.last_idx = idx

        for fix in self._strobing:
            pix_start, pix_end = BufferUtils.get_fixture_extents(fix.strand, fix.address)
            self.mask[pix_start:pix_end] = self._on[fix]
            self._on[fix] = not self._on[fix]
            if progress > self._time[fix] + self._duration:
                self._strobing.remove(fix)
                self.mask[pix_start:pix_end][:] = True

        np.add(struct_flat(start), struct_flat(end), struct_flat(out))
