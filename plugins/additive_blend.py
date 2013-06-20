import numpy as np
import math

from lib.transition import Transition
from lib.buffer_utils import BufferUtils


class AdditiveBlend(Transition):
    """
    Additive HLS blender:
    This approximates color addition for the HLS color space.
    Adding opposite colors produces white.
    Adding other colors aims for a hue midpoint.
    Adding black to a color has no effect
    Adding anything to white is still white.    
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Additive Blend"

    def reset(self):
        self.buffer_len = BufferUtils.get_buffer_size()
        self.frame = np.tile(np.array([0.0], dtype=np.float), (self.buffer_len, 3))

    def get(self, start, end, progress):

        fade_length = 0.25
        ease_power = 2.0
        
        start_transpose = start.T
        end_transpose = end.T
        
        startPower = (1.0 - progress) / fade_length if progress >= (1 - fade_length) else 1.0
        startPower = 1.0 - pow(1.0 - startPower, ease_power)

        endPower = (progress / fade_length) if progress <= fade_length else 1.0
        endPower = 1.0 - pow(1.0 - endPower, ease_power)
        
        startLums = (start_transpose[1] * startPower).clip(0,1)
        endLums = (end_transpose[1] * endPower).clip(0,1)
 
        totalPower = (startPower + endPower)
        
        startHues = np.mod(start_transpose[0], 1.0)
        endHues = np.mod(end_transpose[0], 1.0)
 
        hueDelta = np.abs(startHues - endHues)
        useAlternatePath = np.floor(hueDelta * 2) # path between two colors is 0.5 maximum
        startHues += useAlternatePath # if path too long, go the other way

        startWeight = (1.0 - 2 * np.abs(0.5 - startLums)) * start_transpose[2] + 0.01
        endWeight = (1.0 - 2 * np.abs(0.5 - endLums)) * end_transpose[2] + 0.01
        totalWeight = startWeight + endWeight

        hues = np.mod((startHues * startPower * startWeight + endHues * endPower * endWeight) / totalWeight / totalPower * 2, 1.0)

        # strongly opposing vibrant colors increase **luminance**
        # so that color addition preserves continuous curves
        opposition = 2.0 * np.abs(useAlternatePath - hueDelta) # 0 to 1
        opposition = 1.0 - np.power(1.0 - opposition, 2.0) # 0 to 1 but closer to 1
        opposition *= startWeight * endWeight
        opposition = (opposition * 2.0) - 1.0 # increase contrast on addition whiteouts
        #opposition.clip(0, 1, opposition)
        lums = np.maximum(np.maximum(startLums,endLums), opposition)

        sats = (start_transpose[2] * startWeight + end_transpose[2] * endWeight).clip(0,1)

        self.frame = np.asarray([hues, lums, sats]).T

        """
        if np.random.random() > 0.95:
            print "progress %.2f," % progress, '%.2f' % start[0][0][0], '%.2f' % start[0][0][1], '%.2f' % start[0][0][2], "+", '%.2f' % end[0][0][0], '%.2f' % end[0][0][1], '%.2f' % end[0][0][2], "=", '%.2f' % self.frame[0][0][0], '%.2f' % self.frame[0][0][1], '%.2f' % self.frame[0][0][2]
            print "    delta %.2f" % hueDelta[0][0], useAlternatePath[0][0], "oppo %.2f" % opposition[0][0], "sW %.2f" % startWeight[0][0], "eW %.2f" % endWeight[0][0], "sP %.2f" % startPower, "eP %.2f" % endPower
        """

        return self.frame