import colorsys
import random

from lib.raw_preset import RawPreset
from lib.colors import uint8_to_float, float_to_uint8
from lib.color_fade import ColorFade


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
    _alive_color = (0.35, 1.0, 1.0)  # HSV
    _dead_color = (0.13, 0.87, 0.57)  # HSV
    _growth_time = 0.75  # seconds
    _life_time = 5.0
    _isolated_life_time = 1.0
    _death_time = 1.75
    _fade_out_time = 0.25
    _spontaneous_birth_probability = 0.0001
    _spread_probability = 0.03
    _growth_spread_probability = 0.13
    _mass_destruction_time = 10.0
    _mass_destruction_pop_threshold = 150
    _pop_limit = 500

    # Internal parameters
    _time = {}
    _alive_color_rgb = float_to_uint8(colorsys.hsv_to_rgb(*_alive_color))
    _dead_color_rgb = float_to_uint8(colorsys.hsv_to_rgb(*_dead_color))
    _pop = 0
    _fader = ColorFade('hsv', [(0., 0., 0.), _alive_color, _dead_color, (0., 0., 0.)])

    def draw(self, dt):

        # Ensure that empty displays start up with some seeds
        p_birth = (1.0 - self._spontaneous_birth_probability) if self._pop > 5 else 0.5

        # Spontaneous birth: Rare after startup
        if (self._pop < self._pop_limit) and random.random() > p_birth:
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
            p, color = self._get_next_color(address, self._growth_time, dt)
            if p >= 1.0:
                self._growing.remove(address)
                self._alive.append(address)
                self._time[address] = dt
            self._pixel_buffer[address] = color

            # Spread
            if (self._pop < self._pop_limit) and random.random() > (1.0 - self._growth_spread_probability):
                spread = neighbors[random.randint(0, len(neighbors) - 1)]
                if spread not in (self._growing + self._alive + self._dying + self._fading_out):
                    self._growing.append(spread)
                    self._time[spread] = dt
                    self._pop += 1

        # Lifetime
        for address in self._alive:
            neighbors = self.scene().get_pixel_neighbors(address)
            live_neighbors = [i for i in neighbors if i in self._alive]
            lt = self._life_time
            if len(neighbors) == 0:
                lt = self._isolated_life_time

            if len(live_neighbors) < 2 and ((dt - self._time[address]) / lt) >= 1.0:
                self._alive.remove(address)
                self._dying.append(address)
                self._time[address] = dt
                self._pop -= 1

            self._pixel_buffer[address] = self._alive_color_rgb

            # Spread
            if (self._pop < self._pop_limit) and random.random() > (1.0 - self._spread_probability):
                spread = neighbors[random.randint(0, len(neighbors) - 1)]
                if spread not in (self._growing + self._alive + self._dying + self._fading_out):
                    self._growing.append(spread)
                    self._time[spread] = dt
                    self._pop += 1

        # Color decay
        for address in self._dying:
            p, color = self._get_next_color(address, self._death_time, dt)
            if p >= 1.0:
                self._dying.remove(address)
                self._fading_out.append(address)
                self._time[address] = dt
            self._pixel_buffer[address] = color

        # Fade out
        for address in self._fading_out:
            p, color = self._get_next_color(address, self._fade_out_time, dt)
            if p >= 1.0:
                self._fading_out.remove(address)
            self._pixel_buffer[address] = color

        # Mass destruction
        if (self._pop == self._pop_limit) or \
                (self._pop > self._mass_destruction_pop_threshold and ((dt % self._mass_destruction_time) == 0)):
            for i in self._alive:
                if random.random() > 0.75:
                    self._alive.remove(i)
                    self._dying.append(i)
                    self._pop -= 1
            for i in self._growing:
                if random.random() > 0.75:
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
        if time_target == self._death_time:
            idx += (1.0 / 3.0)
        elif time_target == self._fade_out_time:
            idx += (2.0 / 3.0)

        return (progress, self._fader.get_color(idx))
