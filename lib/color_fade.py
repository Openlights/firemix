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

import unittest
import colorsys
import numpy as np

from lib.colors import clip

class ColorFade:
    """Represents the fade of one color to another"""

    def __init__(self, keyframes, steps):
        """
        keyframes: a list of 3-element tuples representing the colors to fade between.
        """

        self._steps = steps
        self.keyframes = keyframes
        self.color_cache = np.zeros((steps + 1, 3), dtype=np.float32)

        # Warmup the cache
        for i in xrange(steps + 1):
            overall_progress = float(i) * (len(self.keyframes) - 1) / self._steps
            stage = int(overall_progress)
            stage_progress = overall_progress - stage # 0 to 1 float

            # special case stage_progress=0, so if progress=1, we don't get
            # an IndexError
            if stage_progress == 0:
                color = self.keyframes[stage]
            else:
                frame1 = self.keyframes[stage]
                frame1_weight = 1 - stage_progress

                frame2 = self.keyframes[stage + 1]
                frame2_weight = stage_progress

                color = tuple([c1 * frame1_weight + c2 * frame2_weight for c1, c2 in zip(frame1, frame2)])
            self.color_cache[i] = color
#            print progress, self.color_cache[progress]

    def get_color(self, progress):
        """
        Given a progress value between 0 and steps, returns the color for that
        progress as a (h, l, s) tuple with float values
        """

        progress = clip(0, int(progress), self._steps)

        return self.color_cache[progress]


Rainbow = ColorFade([(0, 0.5, 1), (1, 0.5, 1)], 256)
