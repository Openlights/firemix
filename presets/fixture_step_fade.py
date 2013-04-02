from lib.preset import Preset
from lib.color_fade import Rainbow
from lib.basic_tickers import fade, offset, speed, callback



class FixtureStepFade(Preset):
    """
    demonstrates the callback ticker by stepping through a list of fixtures
    and adding fade tickers for a new one every second
    """

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

    groups = [spikes, pentagon, star, spokes, outside]
    all_fixtures = [f for group in groups for f in group]
    idx = 0

    def setup(self):
        self.add_ticker(speed(fade(self.all_fixtures[self.idx], Rainbow), 0.25))
        self.add_ticker(callback(self.advance, 1.0))

    def advance(self):
        if self.idx < len(self.all_fixtures):
            self.idx += 1
            self.add_ticker(speed(fade(self.all_fixtures[self.idx], Rainbow), 0.25))
