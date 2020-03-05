# This file is part of Firemix.
#
# Copyright 2013-2020 Jonathan Evans <jon@craftyjon.com>
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
import math

from lib.transition import Transition
from lib.buffer_utils import BufferUtils


class AdditiveBlend(Transition):
    """
    Additive HLS blender:
    This approximates color addition for the HLS color space.
    This class is pretty glitchy. Use Linear Blend instead if you want smooth results.
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Additive Blend"

    def render(self, start, end, progress, out):

        fade_length = 0.25
        ease_power = 2.0

        startPower = (1.0 - progress) / fade_length if progress >= (1 - fade_length) else 1.0
        startPower = 1.0 - pow(1.0 - startPower, ease_power)

        endPower = (progress / fade_length) if progress <= fade_length else 1.0
        endPower = 1.0 - pow(1.0 - endPower, ease_power)

        startLums = (start['light'] * startPower).clip(0,1)
        endLums = (end['light'] * endPower).clip(0,1)

        totalPower = (startPower + endPower)

        startHues = np.mod(start['hue'], 1.0)
        endHues = np.mod(end['hue'], 1.0)

        hueDelta = np.abs(startHues - endHues)
        useAlternatePath = np.floor(hueDelta * 2) # path between two colors is 0.5 maximum
        startHues += useAlternatePath # if path too long, go the other way

        startWeight = (1.0 - 2 * np.abs(0.5 - startLums)) * start['sat'] + 0.01
        endWeight = (1.0 - 2 * np.abs(0.5 - endLums)) * end['sat'] + 0.01
        totalWeight = startWeight + endWeight

        hues = np.mod((startHues * startPower * startWeight + endHues * endPower * endWeight) / totalWeight / totalPower * 2, 1.0)

        # strongly opposing vibrant colors increase **lightness**
        # so that color addition preserves continuous curves
        opposition = 2.0 * np.abs(useAlternatePath - hueDelta) # 0 to 1
        opposition = 1.0 - np.power(1.0 - opposition, 2.0) # 0 to 1 but closer to 1
        opposition *= startWeight * endWeight
        opposition = (opposition * 2.0) - 1.0 # increase contrast on addition whiteouts
        #opposition.clip(0, 1, opposition)
        lums = np.maximum(np.maximum(startLums,endLums), opposition)

        sats = (start['sat'] * startWeight + end['sat'] * endWeight).clip(0,1)

        out['hue'] = hues
        out['light'] = lums
        out['sat'] = sats
