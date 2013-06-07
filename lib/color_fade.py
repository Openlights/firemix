import unittest
import colorsys

from lib.colors import clip

class ColorFade:
    """Represents the fade of one color to another"""

    def __init__(self, keyframes, tick_rate=None):
        """
        keyframes: a list of 3-element tuples representing the colors to fade between.
        """

        self.keyframes = keyframes
        self.color_cache = {}

        # Warmup the cache if we know the timestep
        if tick_rate is not None:
            for i in range(tick_rate):
                self.get_color(float(i) / tick_rate)


    def get_color(self, progress):
        """
        Given a progress value between 0 and 1, returns the color for that
        progress and a (h, l, s) tuple with float values
        """

        progress = clip(0.0, progress, 1.0)

        color = self.color_cache.get(progress, None)
        if color is None:
            if progress > 1.0:
                progress = 1.0
            
            overall_progress = progress * (len(self.keyframes)-1)
            stage = int(overall_progress)
            stage_progress = overall_progress - stage

            # special case stage_progress=0, so if progress=1, we don't get
            # an IndexError
            if stage_progress == 0:
                return self.keyframes[stage]
                
            frame1 = self.keyframes[stage]
            frame1_weight = 1 - stage_progress

            frame2 = self.keyframes[stage + 1]
            frame2_weight = stage_progress

            color = tuple([c1 * frame1_weight + c2 * frame2_weight for c1, c2 in zip(frame1, frame2)])
            self.color_cache[progress] = color
        return color


Rainbow = ColorFade([(0, 0.5, 1), (1, 0.5, 1)])
RedGreen = ColorFade([(1, 0, 0), (0, 1, 0), (1, 0, 0)]) #rgb
RGB = ColorFade([(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)]) #rgb