import numpy as np

from lib.colors import hls_blend
from lib.transition import Transition

class LinearBlend(Transition):
    """
    "Linear" HLS blender:
    This adds hues as vectors and blends L and S
    """

    def __init__(self, app):
        Transition.__init__(self, app)
        self._buffer = None

    def __str__(self):
        return "Linear Blend"

    def get(self, start, end, progress, fade_length=0.6):
        if self._buffer is None:
            self._buffer = np.empty_like(start)
        return hls_blend(start, end, self._buffer, progress, 'add', fade_length, 0.3)
