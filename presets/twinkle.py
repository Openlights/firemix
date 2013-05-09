import colorsys
import random

from lib.raw_preset import RawPreset
from lib.colors import float_to_uint8
from lib.color_fade import ColorFade
from lib.parameters import FloatParameter, HSVParameter


class Twinkle(RawPreset):
    """Random pixels fade in and out"""

    _fading_up = []
    _fading_down = []
    _time = {}
    _fader = None

    def setup(self):
        random.seed()
        self.add_parameter(FloatParameter('birth-rate', 0.15))
        self.add_parameter(FloatParameter('fade-up-time', 0.25))
        self.add_parameter(FloatParameter('fade-down-time', 2.5))
        self.add_parameter(HSVParameter('on-color', (0.15, 1.0, 1.0)))
        self.add_parameter(HSVParameter('off-color', (0.0, 0.0, 0.0)))
        self._setup_colors()

    def parameter_changed(self, parameter):
        if str(parameter) == 'on-color':
            self._setup_colors()

    def _setup_colors(self):
        self._up_target_rgb = float_to_uint8(colorsys.hsv_to_rgb(*self.parameter('on-color').get()))
        self._down_target_rgb = float_to_uint8(colorsys.hsv_to_rgb(*self.parameter('off-color').get()))
        self._fader = ColorFade('hsv', [self.parameter('off-color').get(), self.parameter('on-color').get()])

    def reset(self):
        self._fading_up = []
        self._fading_down = []
        self._time = {}

    def draw(self, dt):

        # Birth
        if random.random() > (1.0 - self.parameter('birth-rate').get()):
            address = ( random.randint(0, self._max_strand - 1),
                        random.randint(0, self._max_fixture - 1),
                        random.randint(0, self._max_pixel - 1))
            if address not in self._fading_up:
                self._fading_up.append(address)
                self._time[address] = dt

        # Growth
        for address in self._fading_up:
            color = self._get_next_color(address, dt)
            if color == self._up_target_rgb:
                self._fading_up.remove(address)
                self._fading_down.append(address)
                self._time[address] = dt
            self._pixel_buffer[address] = color

        # Decay
        for address in self._fading_down:
            color = self._get_next_color(address, dt, down=True)
            if color == self._down_target_rgb:
                self._fading_down.remove(address)
            self._pixel_buffer[address] = color

    def _get_next_color(self, address, dt, down=False):
        time_target = float(self.parameter('fade-up-time').get()) if down else float(self.parameter('fade-down-time').get())
        progress = (dt - self._time[address]) / time_target

        if progress > 1.0:
            progress = 1.0
        elif dt == self._time[address]:
            progress = 0.0

        if down:
            progress = 1.0 - progress

        return self._fader.get_color(progress)
