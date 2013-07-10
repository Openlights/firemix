from lib.colors import hsl_blend
from lib.transition import Transition

class LinearBlend(Transition):
    """
    "Linear" HLS blender:
    This adds hues as vectors and blends L and S
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Linear Blend"

    def get(self, start, end, progress, fade_length=0.5):

        return hsl_blend(start, end, progress, 'add', fade_length)