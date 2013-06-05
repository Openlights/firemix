import unittest
import colorsys

_color_sys_converters = {
    "rgb": lambda r, g, b: (r, g, b),
    "hls": colorsys.hls_to_rgb,
    "hsv": colorsys.hsv_to_rgb,
    "yiq": colorsys.yiq_to_rgb
}

class ColorFade:
    """Represents the fade of one color to another"""

    def __init__(self, sys, keyframes, tick_rate=None):
        """
        sys: one of "rgb", "hsv", "hls", or "yiq"
        keyframes: a list of 3-element tuples representing the colors to fade
                   between. each element should be between 0 and 1.
        """

        self.sys = sys
        self.keyframes = keyframes
        self.color_cache = {}

        # Warmup the cache if we know the timestep
        if tick_rate is not None:
            for i in range(tick_rate):
                self.get_color(float(i) / tick_rate)


    def get_color(self, progress):
        """
        Given a progress value between 0 and 1, returns the color for that
        progress and a (r, g, b) tuple with float values between 0 and 1
        """

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
                c = self._convert_to_rgb(self.keyframes[stage])
                return tuple([int(255.0 * el) for el in c])          
                
            frame1 = self.keyframes[stage]
            frame1_weight = 1 - stage_progress

            frame2 = self.keyframes[stage + 1]
            frame2_weight = stage_progress

            float_color = self._convert_to_rgb(tuple([c1 * frame1_weight + c2 * frame2_weight for c1, c2 in zip(frame1, frame2)]))
            color = tuple([int(255.0 * el) for el in float_color])
            self.color_cache[progress] = color
        return color

    def _convert_to_rgb(self, triplet):
        """converts a triplet in this ColorFade's color system to an rgb triplet"""

        return _color_sys_converters[self.sys](*triplet)

Rainbow = ColorFade("hsv", [(0, 1, 1), (1, 1, 1)])
RedGreen = ColorFade("rgb", [(1, 0, 0), (0, 1, 0), (1, 0, 0)])
RGB = ColorFade("rgb", [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)])


class TestColorFade(unittest.TestCase):

    def test_two_color_hsv(self):
        uut = ColorFade("hsv", [(0, 1, 1), (1, 1, 1)])
        self.assertEqual(uut.get_color(0), (1.0, 0, 0))
        self.assertEqual(uut.get_color(0.5), (0, 1.0, 1.0))
        self.assertEqual(uut.get_color(1.0), (1.0, 0, 0))

    def test_three_color_rgb(self):
        uut = ColorFade("rgb", [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)])
        self.assertEqual(uut.get_color(0), (1.0, 0, 0))
        self.assertEqual(uut.get_color(0.5), (0, 0.5, 0.5))
        self.assertEqual(uut.get_color(0.75), (0.25, 0, 0.75))
        self.assertEqual(uut.get_color(1.0), (1.0, 0, 0))