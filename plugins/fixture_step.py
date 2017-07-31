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

from lib.transition import Transition
from lib.buffer_utils import BufferUtils, struct_flat


class FixtureStep(Transition):
    """
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Fixture Step"

    def reset(self):
        self.fixtures = self._app.scene.fixtures()
        buffer_size = BufferUtils.get_buffer_size()
        self.mask = np.tile(False, buffer_size)

        np.random.seed()
        self.rand_index = np.arange(len(self.fixtures))
        np.random.shuffle(self.rand_index)

        self.last_idx = 0

    def get(self, start, end, progress):
        start[self.mask] = (0.0, 0.0, 0.0)
        end[np.invert(self.mask)] = (0.0, 0.0, 0.0)

        idx = int(progress * len(self.rand_index))

        if idx >= self.last_idx:
            for i in range(self.last_idx, idx):
                fix = self.fixtures[self.rand_index[i]]
                pix_start, pix_end = BufferUtils.get_fixture_extents(fix.strand, fix.address)
                self.mask[pix_start:pix_end] = True
        else:
            for i in range(idx, self.last_idx):
                fix = self.fixtures[self.rand_index[i]]
                pix_start, pix_end = BufferUtils.get_fixture_extents(fix.strand, fix.address)
                self.mask[pix_start:pix_end]= False

        self.last_idx = idx

        out = np.empty_like(start)
        np.add(struct_flat(start), struct_flat(end), struct_flat(out))
        return out

