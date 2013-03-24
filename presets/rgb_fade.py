import colorsys

from lib.preset import Preset
from lib.basic_tickers import fade, speed
from lib.color_fade import Rainbow

class RGBFade(Preset):
    """Simple RGB fade"""

    h = 0.0

    def setup(self):
        self.add_ticker( speed(fade((), Rainbow), 0.2) )

