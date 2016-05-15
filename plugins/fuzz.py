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
from lib.buffer_utils import BufferUtils


class Fuzz(Transition):
    """
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Fuzz"

    def reset(self):
        self.buffer_size = BufferUtils.get_buffer_size()
        self.mask = np.tile(False, (self.buffer_size, 3))

        num_elements = np.ndarray.flatten(self.mask).size / 3
        np.random.seed()
        self.rand_index = np.arange(num_elements)
        np.random.shuffle(self.rand_index)

        self.last_idx = 0


    def get(self, start, end, progress):
        idx = int(progress * len(self.rand_index))
        for i in range(self.last_idx, idx):
            offset = self.rand_index[i] * 3
            self.mask.flat[offset] = True
            self.mask.flat[offset + 1] = True
            self.mask.flat[offset + 2] = True
        self.last_idx = idx

        start[self.mask] = 0.0
        end[np.invert(self.mask)] = 0.0

        return (start) + (end)
