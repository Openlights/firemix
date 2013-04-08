from lib.preset import Preset
from lib.color_fade import Rainbow
from lib.basic_tickers import fade, offset


class SeparateStrandRGB(Preset):
    outside = [(0, 0),
               (0, 1),
               (0, 2),
               (0, 3),
               (0, 4),
               (0, 5),
               (0, 6),
               (0, 7),
               (0, 8),
               (0, 9)]

    spokes = [(1, 0),
              (1, 3),
              (1, 6),
              (2, 1),
              (2, 4)]

    star = [(1, 1),
            (1, 2),
            (1, 4),
            (1, 5),
            (1, 7),
            (2, 0),
            (2, 2),
            (2, 3),
            (2, 5),
            (2, 6)]

    pentagon = [(3, 0),
                (3, 1),
                (3, 2),
                (3, 3),
                (3, 4)]

    spikes = [(3, 5),
              (3, 6),
              (3, 7),
              (3, 8),
              (3, 9)]

    def setup(self):
        self.add_ticker(fade((0,), Rainbow))  # The outside is the entirety of strand zero.
        self.add_ticker(offset(fade(self.spokes, Rainbow), 0.05))
        self.add_ticker(offset(fade(self.star, Rainbow), 0.1))
        self.add_ticker(offset(fade(self.pentagon, Rainbow), 0.15))
        self.add_ticker(offset(fade(self.spikes, Rainbow), 0.2))