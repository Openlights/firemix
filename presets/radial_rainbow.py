import math

from lib.preset import Preset
from lib.color_fade import Rainbow
from lib.basic_tickers import fade, offset, speed
from lib.parameters import FloatParameter


class RadialRainbow(Preset):
    """
    demonstrates scene attributes by assigning a color rainbow
    to fixtures based on their radial position in the scene
    """

    def setup(self):
        self.add_parameter(FloatParameter('speed', 0.2))
        self.add_parameter(FloatParameter('width', 1.0))
        self._create_tickers()

    def parameter_changed(self, parameter):
        if str(parameter) == 'width':
            self._create_tickers()

    def _create_tickers(self):
        fixtures = self.scene().fixtures()
        midpoint_tuples = [(f.strand(), f.address(), f.midpoint()) for f in fixtures]
        extents = self.scene().extents()
        center = tuple([0.5 * c for c in extents])
        for strand, address, midpoint in midpoint_tuples:
            dx, dy = (midpoint[0] - center[0], midpoint[1] - center[1])
            angle = (math.pi + math.atan2(dy, dx)) / (2.0 * math.pi) * self.parameter('width').get()
            self.add_ticker(speed(offset(fade((strand, address), Rainbow), angle), self.parameter('speed')))
