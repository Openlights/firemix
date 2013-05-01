import colorsys
import random

from lib.raw_preset import RawPreset
from lib.colors import uint8_to_float, float_to_uint8


class Fireflies(RawPreset):
    """Random decaying fireflies"""

    _fading_up = []
    _fading_down = []

    # Configurable parameters
    _up_target = (0.16, 1.0, 1.0)  # HSV
    _down_target = (0.0, 0.0, 0.0)  # HSV
    _fade_up_time = 0.5  # seconds
    _fade_down_time = 3

    # Internal parameters
    _total_delta = tuple(map(lambda x, y: x - y, _up_target, _down_target))
    _time = {}
    _up_target_rgb = colorsys.hsv_to_rgb(*_up_target)
    _down_target_rgb = colorsys.hsv_to_rgb(*_down_target)

    def setup(self):
        pass

    def draw(self, dt):

        # Birth
        if random.random() > 0.9:
            address = ( random.randint(0, self._max_strand - 1),
                        random.randint(0, self._max_fixture - 1),
                        random.randint(0, self._max_pixel - 1))
            if address not in self._fading_up:
                self._fading_up.append(address)
                self._time[address] = dt
                #print self._fading_up

        # Growth
        for address in self._fading_up:
            color = self._get_next_color(address, uint8_to_float(self.current_color(address)), dt)
            if color == self._up_target_rgb:
                self._fading_up.remove(address)
                self._fading_down.append(address)
                self._time[address] = dt
            self._pixel_buffer[address] = float_to_uint8(color)

        # Decay
        for address in self._fading_down:
            color = self._get_next_color(address, uint8_to_float(self.current_color(address)), dt, down=True)
            if color == self._down_target_rgb:
                #print "Dead"
                self._fading_down.remove(address)
            self._pixel_buffer[address] = float_to_uint8(color)

    def _get_next_color(self, address, color, dt, down=False):
        if dt == self._time[address]:
            return tuple(color)

        time_target = float(self._fade_down_time) if down else float(self._fade_up_time)
        progress = (dt - self._time[address]) / time_target
        target = self._down_target if down else self._up_target

        if progress > 1.0:
            progress = 1.0

        if progress == 1.0:
            return colorsys.hsv_to_rgb(target[0], target[1], target[2])

        if down:
            progress = 1.0 - progress
            #print progress

        #print "progress", progress

        nc = tuple(map(lambda x: x * progress, self._total_delta))
        #print "new_hsv", new_hsv

        if (nc[0] < 0) or (nc[1] < 0) or (nc[2] < 0) or (nc[0] > 1) or (nc[1] > 1) or (nc[2] > 1):
            print "WARN", nc
            print "progress", progress

        return colorsys.hsv_to_rgb(nc[0], nc[1], nc[2])
