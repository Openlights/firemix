import colorsys
import math

from lib.preset import Preset


class SeparateStrandRGB(Preset):
    """Simple RGB fade using separate groups of fixtures.

    In this example, fixtures are stored as groups of (strand, fixture) tuples.
    This makes it easy to assign certain colors to groups.
    """

    h = 0.0

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

    groups = [outside, spokes, star, pentagon, spikes]

    def setup(self):
        pass

    def tick(self):
        for i, group in enumerate(self.groups):
            rgb_color = [int(255.0 * c) for c in colorsys.hsv_to_rgb(math.fmod(self.h + (i / 7.0), 1.0), 1.0, 1.0)]
            for sf in group:
                strand, fixture = sf
                self.set_fixture(strand, fixture, rgb_color)

        self.h += 0.0001 * self.tick_rate()
        if self.h > 1.0:
            self.h = 0.0
