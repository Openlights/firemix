import colorsys
import random

from lib.raw_preset import RawPreset
from lib.colors import uint8_to_float, float_to_uint8
from lib.color_fade import ColorFade
from lib.parameters import FloatParameter, IntParameter, HSVParameter


class Fungus(RawPreset):
    """
    Spreading fungus
    Illustrates use of Scene.get_pixel_neighbors.

    Fungal pixels go through three stages:  Growing, Dying, and then Fading Out.
    """

    _growing = []
    _alive = []
    _dying = []
    _fading_out = []

    # Configurable parameters
    _spontaneous_birth_probability = 0.0001

    # Internal parameters
    _time = {}
    _pop = 0
    _fader = None


    def setup(self):
        self._pop = 0
        self._time = {}
        self.add_parameter(FloatParameter('growth-time', 0.75))
        self.add_parameter(FloatParameter('life-time', 5.0))
        self.add_parameter(FloatParameter('isolated-life-time', 1.0))
        self.add_parameter(FloatParameter('death-time', 1.75))
        self.add_parameter(FloatParameter('birth-rate', 0.03))
        self.add_parameter(FloatParameter('spread-rate', 0.13))
        self.add_parameter(FloatParameter('fade-out-time', 0.25))
        self.add_parameter(FloatParameter('mass-destruction-time', 10.0))
        self.add_parameter(IntParameter('mass-destruction-threshold', 150))
        self.add_parameter(IntParameter('pop-limit', 500))
        self.add_parameter(HSVParameter('alive-color', (0.35, 1.0, 1.0)))
        self.add_parameter(HSVParameter('dead-color', (0.13, 0.87, 0.57)))
        self._setup_colors()

    def reset(self):
        self._growing = []
        self._alive = []
        self._dying = []
        self._fading_out = []
        self._pop = 0
        self._time = {}

    def parameter_changed(self, parameter):
        self._setup_colors()

    def _setup_colors(self):
        self._alive_color_rgb = float_to_uint8(colorsys.hsv_to_rgb(*self.parameter('alive-color').get()))
        self._dead_color_rgb = float_to_uint8(colorsys.hsv_to_rgb(*self.parameter('dead-color').get()))
        self._fader = ColorFade('hsv', [(0., 0., 0.), self.parameter('alive-color').get(), self.parameter('dead-color').get(), (0., 0., 0.)])

    def draw(self, dt):

        # Ensure that empty displays start up with some seeds
        p_birth = (1.0 - self._spontaneous_birth_probability) if self._pop > 5 else 0.5

        # Spontaneous birth: Rare after startup
        if (self._pop < self.parameter('pop-limit').get()) and random.random() > p_birth:
            address = ( random.randint(0, self._max_strand - 1),
                        random.randint(0, self._max_fixture - 1),
                        random.randint(0, self._max_pixel - 1))
            if address not in (self._growing + self._alive + self._dying + self._fading_out):
                self._growing.append(address)
                self._time[address] = dt
                self._pop += 1

        # Color growth
        for address in self._growing:
            neighbors = self.scene().get_pixel_neighbors(address)
            p, color = self._get_next_color(address, self.parameter('growth-time').get(), dt)
            if p >= 1.0:
                self._growing.remove(address)
                self._alive.append(address)
                self._time[address] = dt
            self._pixel_buffer[address] = color

            # Spread
            if (self._pop < self.parameter('pop-limit').get()) and random.random() > (1.0 - self.parameter('spread-rate').get()):
                spread = neighbors[random.randint(0, len(neighbors) - 1)]
                if spread not in (self._growing + self._alive + self._dying + self._fading_out):
                    self._growing.append(spread)
                    self._time[spread] = dt
                    self._pop += 1

        # Lifetime
        for address in self._alive:
            neighbors = self.scene().get_pixel_neighbors(address)
            live_neighbors = [i for i in neighbors if i in self._alive]
            lt = self.parameter('life-time').get()
            if len(neighbors) < 2:
                lt = self.parameter('isolated-life-time').get()

            if len(live_neighbors) < 2 and ((dt - self._time[address]) / lt) >= 1.0:
                self._alive.remove(address)
                self._dying.append(address)
                self._time[address] = dt
                self._pop -= 1

            self._pixel_buffer[address] = self._alive_color_rgb

            # Spread
            if (self._pop < self.parameter('pop-limit').get()) and random.random() > (1.0 - self.parameter('birth-rate').get()):
                spread = neighbors[random.randint(0, len(neighbors) - 1)]
                if spread not in (self._growing + self._alive + self._dying + self._fading_out):
                    self._growing.append(spread)
                    self._time[spread] = dt
                    self._pop += 1

        # Color decay
        for address in self._dying:
            p, color = self._get_next_color(address, self.parameter('death-time').get(), dt)
            if p >= 1.0:
                self._dying.remove(address)
                self._fading_out.append(address)
                self._time[address] = dt
            self._pixel_buffer[address] = color

        # Fade out
        for address in self._fading_out:
            p, color = self._get_next_color(address, self.parameter('fade-out-time').get(), dt)
            if p >= 1.0:
                self._fading_out.remove(address)
            self._pixel_buffer[address] = color

        # Mass destruction
        if (self._pop == self.parameter('pop-limit').get()) or \
                (self._pop > self.parameter('mass-destruction-threshold').get() and ((dt % self.parameter('mass-destruction-time').get()) == 0)):
            for i in self._alive:
                if random.random() > 0.95:
                    self._alive.remove(i)
                    self._dying.append(i)
                    self._pop -= 1
            for i in self._growing:
                if random.random() > 0.85:
                    self._growing.remove(i)
                    self._dying.append(i)
                    self._pop -= 1

    def _get_next_color(self, address, time_target, dt):
        """
        Returns the next color for a pixel, given the pixel's current state
        """
        progress = (dt - self._time[address]) / time_target

        if progress > 1.0:
            progress = 1.0
        elif dt == self._time[address]:
            progress = 0.0

        idx = progress / 3.0
        if time_target == self.parameter('death-time').get():
            idx += (1.0 / 3.0)
        elif time_target == self.parameter('fade-out-time').get():
            idx += (2.0 / 3.0)

        return (progress, self._fader.get_color(idx))
