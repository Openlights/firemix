from lib.preset import Preset
from lib.color_fade import Rainbow
from lib.basic_tickers import fade, offset


class SeparateStrandRGB(Preset):
    outside = [(0, 0),
               (1, 0),
               (1, 3),
               (1, 4),
               (3, 0),
               (3, 4),
               (5, 0),
               (5, 1),
               (5, 2),
               (0, 3)]

    spokes = [(0, 2),
              (1, 2),
              (2, 0),
              (4, 0),
              (5, 4)]

    star = [(0, 1),
            (1, 1),
            (2, 2),
            (2, 1),
            (3, 1),
            (3, 3),
            (4, 1),
            (4, 2),
            (5, 3),
            (0, 4)]

    pentagon = [(6, 0),
                (2, 3),
                (3, 2),
                (4, 3),
                (6, 3)]

    spikes = [(6, 2),
              (6, 1),
              (2, 4),
              (4, 4),
              (6, 4)]

    def setup(self):
        self.add_ticker(fade((0,), Rainbow))  # The outside is the entirety of strand zero.
        self.add_ticker(offset(fade(self.spokes, Rainbow), 0.05))
        self.add_ticker(offset(fade(self.star, Rainbow), 0.1))
        self.add_ticker(offset(fade(self.pentagon, Rainbow), 0.15))
        self.add_ticker(offset(fade(self.spikes, Rainbow), 0.2))