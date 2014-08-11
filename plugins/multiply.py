import numpy as np

from lib.colors import hls_blend
from lib.transition import Transition

class MultiplyBlend(Transition):
    """
    This approximates color subtraction for the HLS color space.
    """

    def __init__(self, app):
        Transition.__init__(self, app)
        self._buffer = None

    def __str__(self):
        return "Multiply Blend"

    def get(self, start, end, progress, fade_length=0.5):
        if self._buffer is None:
            self._buffer = np.empty_like(start)
        return hls_blend(start, end, self._buffer, progress, 'multiply', fade_length, 0.5)
