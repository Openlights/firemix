import colorsys
import random

from lib.raw_preset import RawPreset
from lib.colors import uint8_to_float, float_to_uint8
from lib.color_fade import ColorFade


class Fireflies(RawPreset):
    """Random decaying fireflies"""

    _fading_up = []
    _fading_down = []

    # Configurable parameters
    _up_target = (0.15, 1.0, 1.0)  # HSV
    _down_target = (0.0, 0.0, 0.0)  # HSV
    _fade_up_time = 0.25  # seconds
    _fade_down_time = 2.5
    _birth_rate = 0.15

    # Internal parameters
    _total_delta = tuple(map(lambda x, y: x - y, _up_target, _down_target))
    _time = {}
    _up_target_rgb = float_to_uint8(colorsys.hsv_to_rgb(*_up_target))
    _down_target_rgb = float_to_uint8(colorsys.hsv_to_rgb(*_down_target))

    _fader = ColorFade('hsv', [_down_target, _up_target])

    def draw(self, dt):

        # Birth
        if random.random() > (1.0 - self._birth_rate):
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
        time_target = float(self._fade_down_time) if down else float(self._fade_up_time)
        progress = (dt - self._time[address]) / time_target

        if progress > 1.0:
            progress = 1.0
        elif dt == self._time[address]:
            progress = 0.0

        if down:
            progress = 1.0 - progress

        return self._fader.get_color(progress)
