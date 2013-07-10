from lib.colors import hsl_blend
from lib.transition import Transition

class MultiplyBlend(Transition):
    """
    This approximates color subtraction for the HLS color space.
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Multiply Blend"

    def get(self, start, end, progress, fade_length=0.5):

        #l = np.sqrt(np.square((x1-x2)) + np.square((y1-y2)))
        #l = (2.0 - (2.0 - l1 * 2) * startPower) * (2.0 - (2.0 - l2 * 2) * endPower) / 2
        #print l1, l2, startPower, endPower, l
        #l = np.minimum(l, l1 * startPower + l2 * endPower, l)

        return hsl_blend(start, end, progress, 'multiply', fade_length)
