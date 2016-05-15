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

from lib.colors import hls_blend
from lib.transition import Transition

class Dissolve(Transition):

    def __init__(self, app):
        Transition.__init__(self, app)
        self._buffer = None

    def __str__(self):
        return "Dissolve"

    def get(self, start, end, progress, fade_length = 1.0):
        if self._buffer is None:
            self._buffer = np.empty_like(start)
        return hls_blend(start, end, self._buffer, progress, 'add', fade_length, 1.0)
