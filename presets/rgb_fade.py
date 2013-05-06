from lib.preset import Preset
from lib.basic_tickers import fade, speed
from lib.color_fade import Rainbow
from lib.parameters import FloatParameter

class RGBFade(Preset):
    """Simple RGB fade"""

    def setup(self):
        self.add_parameter(FloatParameter('speed', 0.2))
        self.add_ticker(speed(fade((), Rainbow), self.parameter('speed')))
