import unittest
import colorsys
import numpy as np

from lib.colors import clip

class ColorFade:
    """Represents the fade of one color to another"""

    def __init__(self, keyframes, steps):
        """
        keyframes: a list of 3-element tuples representing the colors to fade between.
        """

        self._steps = steps
        self.keyframes = keyframes
        self.color_cache = np.zeros((steps + 1, 3), dtype=np.float32)

        # Warmup the cache
        for i in xrange(steps + 1):
            overall_progress = float(i) * (len(self.keyframes) - 1) / self._steps
            stage = int(overall_progress)
            stage_progress = overall_progress - stage # 0 to 1 float

            # special case stage_progress=0, so if progress=1, we don't get
            # an IndexError
            if stage_progress == 0:
                color = self.keyframes[stage]
            else:
                frame1 = self.keyframes[stage]
                frame1_weight = 1 - stage_progress

                frame2 = self.keyframes[stage + 1]
                frame2_weight = stage_progress

                color = tuple([c1 * frame1_weight + c2 * frame2_weight for c1, c2 in zip(frame1, frame2)])
            self.color_cache[i] = color
#            print progress, self.color_cache[progress]

    def get_color(self, progress):
        """
        Given a progress value between 0 and steps, returns the color for that
        progress as a (h, l, s) tuple with float values
        """

        progress = clip(0, int(progress), self._steps)

        return self.color_cache[progress]


Rainbow = ColorFade([(0, 0.5, 1), (1, 0.5, 1)], 256)