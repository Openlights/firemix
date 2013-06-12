import colorsys
import random
import math

from lib.raw_preset import RawPreset
from lib.colors import float_to_uint8
from lib.color_fade import ColorFade
from lib.parameters import FloatParameter, HLSParameter


class Twinkle(RawPreset):
    """Random pixels fade in and out"""

    _fading_up = []
    _fading_down = []
    _time = {}
    _fader = None

    def setup(self):
        random.seed()
        self.add_parameter(FloatParameter('birth-rate', 0.15))
        self.add_parameter(FloatParameter('fade-up-time', 0.5))
        self.add_parameter(FloatParameter('fade-down-time', 4.0))
        self.add_parameter(HLSParameter('on-color', (0.1, 1.0, 1.0)))
        self.add_parameter(HLSParameter('off-color', (1.0, 0.0, 1.0)))
        self.add_parameter(HLSParameter('beat-color', (1.0, 1.0, 1.0)))
        self._setup_colors()
        self._nbirth = 0;
        self._current_time = 0;

    def parameter_changed(self, parameter):
        if str(parameter) == 'on-color':
            self._setup_colors()

    def _setup_colors(self):
        self._up_target = self.parameter('on-color').get()
        self._down_target = self.parameter('off-color').get()
        self._fader = ColorFade([self.parameter('off-color').get(), self.parameter('on-color').get()])

    def reset(self):
        self._fading_up = []
        self._fading_down = []
        self._idle = self.scene().get_all_pixels()[:]
        self._time = {}

    def draw(self, dt):

        self._current_time += dt
        
        # Birth
        if self._mixer.is_onset():
            self._nbirth += 25
        
        self._nbirth += self.parameter('birth-rate').get()

        for i in range(int(self._nbirth)):
            if (len(self._idle) > 0) and (random.random() < self._nbirth):
                address = self._idle.pop(random.randint(0, len(self._idle) - 1))
                self._fading_up.append(address)
                self._time[address] = self._current_time
                self._nbirth -= 1

        # Growth
        for address in self._fading_up:
            color = self._get_next_color(address, self._current_time)
            if color == self._up_target:
                self._fading_up.remove(address)
                self._fading_down.append(address)
                self._time[address] = self._current_time
            self.setPixelHLS(address, color)

        # Decay
        for address in self._fading_down:
            color = self._get_next_color(address, self._current_time, down=True)
            if color == self._down_target:
                self._idle.append(address)
                self._fading_down.remove(address)
            if self._mixer.is_onset():
                self.setPixelHLS(address, self.parameter('beat-color').get())
            else:
                self.setPixelHLS(address, color)                

    def _get_next_color(self, address, time, down=False):
        time_target = float(self.parameter('fade-down-time').get()) if down else float(self.parameter('fade-up-time').get())
        progress = (time - self._time[address]) / time_target

        if progress > 1.0:
            progress = 1.0
        elif time == self._time[address]:
            progress = 0.0

        if down:
            progress = 1.0 - progress

        return self._fader.get_color(progress)
