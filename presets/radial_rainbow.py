import math

from lib.preset import Preset
from lib.color_fade import Rainbow
from lib.basic_tickers import fade, offset



class RadialRainbow(Preset):
    """
    demonstrates scene attributes by assigning a color rainbow
    to fixtures based on their radial position in the scene
    """

    def setup(self):
        fixtures = self.scene().fixtures()
        midpoint_tuples = [(f.strand(), f.address(), f.midpoint()) for f in fixtures]
        extents = self.scene().extents()
        center = tuple([0.5 * c for c in extents])
        for strand, address, midpoint in midpoint_tuples:
            dx, dy = (midpoint[0] - center[0], midpoint[1] - center[1])
            angle = (math.pi + math.atan2(dy, dx)) / (2.0 * math.pi)
            #print strand, address, midpoint, angle
            self.add_ticker(offset(fade((strand, address), Rainbow), angle))
