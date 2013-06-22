import numpy as np
import math

from lib.transition import Transition
from lib.buffer_utils import BufferUtils


class LinearBlend(Transition):
    """
    "Linear" HLS blender:
    This adds hues as vectors and blends L and S
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Linear Blend"

    def reset(self):
        self.buffer_len = BufferUtils.get_buffer_size()
        self.frame = np.tile(np.array([0.0], dtype=np.float), (self.buffer_len, 3))

    def get(self, start, end, progress):

        fade_length = 0.25
        ease_power = 2.0
        
        startPower = (1.0 - progress) / fade_length if progress >= (1 - fade_length) else 1.0
        startPower = 1.0 - pow(1.0 - startPower, ease_power)

        endPower = (progress / fade_length) if progress <= fade_length else 1.0
        endPower = 1.0 - pow(1.0 - endPower, ease_power)

        h1,l1,s1 = start.T
        h2,l2,s2 = end.T

        np.clip(l1,0,1,l1)
        np.clip(l2,0,1,l2)
        np.clip(s1,0,1,s1)
        np.clip(s2,0,1,s2)
        h1 = np.mod(h1, 1.0)
        h2 = np.mod(h2, 1.0)

        startWeight = (1.0 - 2 * np.abs(0.5 - l1)) * s1
        endWeight = (1.0 - 2 * np.abs(0.5 - l2)) * s2

        s = 0.5 * (s1 + s2)
        #l = 0.5 * (l1 + l2)
        x = np.cos(2 * np.pi * h1) * startPower * startWeight + np.cos(2 * np.pi * h2) * endPower * endWeight
        y = np.sin(2 * np.pi * h1) * startPower * startWeight + np.sin(2 * np.pi * h2) * endPower * endWeight
        l = np.sqrt(np.square(x) + np.square(y))

        h = np.arctan2(y, x) / (2*np.pi)

        nocolor = (x * y == 0)
        np.where(nocolor, h, 0)
        np.where(nocolor, s, 0)

        np.clip(l / 2, 0, 1, l)

        self.frame = np.asarray([h, l, s]).T

        return self.frame