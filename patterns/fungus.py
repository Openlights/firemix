# This file is part of Firemix.
#
# Copyright 2013-2016 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Firemix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Firemix.  If not, see <http://www.gnu.org/licenses/>.

import colorsys
import random

from lib.pattern import Pattern
from lib.colors import uint8_to_float, float_to_uint8
from lib.buffer_utils import BufferUtils
from lib.color_fade import ColorFade
from lib.parameters import FloatParameter, IntParameter, HLSParameter


class Fungus(Pattern):
    """
    Spreading fungus
    Illustrates use of Scene.get_pixel_neighbors.

    Fungal pixels go through three stages:  Growing, Dying, and then Fading Out.
    """

    _growing = []
    _alive = []
    _dying = []
    _fading_out = []
    _fader_steps = 256

    # Configurable parameters
    _spontaneous_birth_probability = 0.0001

    # Internal parameters
    _time = {}
    _population = 0
    _fader = None
    
    _growth_time = 0.6    
    _life_time = 0.5
    _isolated_life_time = 1.0
    _death_time = 3.0
    _birth_rate = 0.05
    _spread_rate = 0.25
    _fade_out_time = 2.0
    _mass_destruction_countdown = 2.0
    _mass_destruction_threshold = 150
    _population_limit = 500
    _alive_color = (1.0, 1.0, 1.0)
    _dead_color = (0.0, 0.5, 1.0)
    _black_color = (0.0, 0.0, 1.0)

    def setup(self):
        self._population = 0
        self._time = {}
        self.add_parameter(FloatParameter('audio-onset-spread-boost', 0.0))
        self.add_parameter(FloatParameter('audio-onset-spread-boost-echo', 0.5))
        self.add_parameter(FloatParameter('audio-onset-death-boost', 0.0))
        self.add_parameter(FloatParameter('audio-onset-birth-boost', 0.0))
        self.add_parameter(FloatParameter('growth-time', self._growth_time))
        self.add_parameter(FloatParameter('life-time', self._life_time))
        self.add_parameter(FloatParameter('isolated-life-time', self._isolated_life_time))
        self.add_parameter(FloatParameter('death-time', self._death_time))
        self.add_parameter(FloatParameter('birth-rate', self._birth_rate))
        self.add_parameter(FloatParameter('spread-rate', self._spread_rate))
        self.add_parameter(FloatParameter('fade-out-time', self._fade_out_time))
        self.add_parameter(FloatParameter('mass-destruction-time', self._mass_destruction_countdown))
        self.add_parameter(IntParameter('mass-destruction-threshold', self._mass_destruction_threshold))
        self.add_parameter(IntParameter('pop-limit', self._population_limit))
        self.add_parameter(HLSParameter('alive-color', self._alive_color))
        self.add_parameter(HLSParameter('dead-color', self._dead_color))
        self.add_parameter(HLSParameter('black-color', self._black_color))
        super(Fungus, self).setup()

    def reset(self):
        self._current_time = 0
        self._growing = []
        self._alive = []
        self._dying = []
        self._fading_out = []
        self._population = 0
        self._time = {}
        self._spread_boost = 0
        self.parameter_changed(None)

    def parameter_changed(self, parameter):
        self._setup_colors()
        self._growth_time = self.parameter('growth-time').get()
        self._life_time = self.parameter('life-time').get()
        self._isolated_life_time = self.parameter('isolated-life-time').get()
        self._death_time = self.parameter('death-time').get()
        self._birth_rate = self.parameter('birth-rate').get()
        self._spread_rate = self.parameter('spread-rate').get()
        self._fade_out_time = self.parameter('fade-out-time').get()
        self._mass_destruction_countdown = self.parameter('mass-destruction-time').get()
        self._mass_destruction_threshold = self.parameter('mass-destruction-threshold').get()
        self._population_limit = self._population_limit

    def _setup_colors(self):
        self._alive_color = self.parameter('alive-color').get()
        self._dead_color = self.parameter('dead-color').get()
        self._black_color = self.parameter('black-color').get()
        fade_colors = [self._black_color, self._alive_color, self._dead_color, self._black_color]
        self._fader = ColorFade(fade_colors, self._fader_steps)

    def draw(self, dt):

        self._current_time += dt
        self._mass_destruction_countdown -= dt
    
        # Ensure that empty displays start up with some seeds
        p_birth = (1.0 - self._spontaneous_birth_probability) if self._population > 5 else 0.5

        # Spontaneous birth: Rare after startup
        if (self._population < self._population_limit) and random.random() + self.parameter('audio-onset-birth-boost').get() > p_birth:
            strand = random.randint(0, BufferUtils.num_strands - 1)
            fixture = random.randint(0, BufferUtils.strand_num_fixtures(strand) - 1)
            pixel = random.randint(0, BufferUtils.fixture_length(strand, fixture) - 1)
            address = BufferUtils.logical_to_index((strand, fixture, pixel))
            if address not in (self._growing + self._alive + self._dying + self._fading_out):
                self._growing.append(address)
                self._time[address] = self._current_time
                self._population += 1

        self._spread_boost *= self.parameter('audio-onset-spread-boost-echo').get()
        if self._mixer.is_onset():
            self._spread_boost += self.parameter('audio-onset-spread-boost').get()

        # Color growth
        for address in self._growing:
            neighbors = self.scene().get_pixel_neighbors(address)
            p, color = self._get_next_color(address, self._growth_time, self._current_time)
            if p >= 1.0:
                self._growing.remove(address)
                self._alive.append(address)
                self._time[address] = self._current_time
            self.setPixelHLS(address, color)

            # Spread
            spread_rate = self._spread_rate + self._spread_boost

            if (self._population < self._population_limit) and (random.random() < spread_rate * dt):
                for spread in neighbors:
                    if spread not in (self._growing + self._alive + self._dying + self._fading_out):
                        self._growing.append(spread)
                        self._time[spread] = self._current_time
                        self._population += 1

        # Lifetime
        for address in self._alive:
            neighbors = self.scene().get_pixel_neighbors(address)
            live_neighbors = [i for i in neighbors if i in self._alive]
            lt = self._life_time
            if len(neighbors) < 2:
                lt = self._isolated_life_time

            if len(live_neighbors) < 3 and ((self._current_time - self._time[address]) / lt) >= 1.0:
                self._alive.remove(address)
                self._dying.append(address)
                self._time[address] = self._current_time
                self._population -= 1

            self.setPixelHLS(address, self._alive_color)

            # Spread
            if (self._population < self._population_limit) and random.random() < self._birth_rate * dt:
                for spread in neighbors:
                    if spread not in (self._growing + self._alive + self._dying + self._fading_out):
                        self._growing.append(spread)
                        self._time[spread] = self._current_time
                        self._population += 1

        # Color decay
        for address in self._dying:
            p, color = self._get_next_color(address, self._death_time, self._current_time + self.parameter('audio-onset-death-boost').get())
            if p >= 1.0:
                self._dying.remove(address)
                self._fading_out.append(address)
                self._time[address] = self._current_time
            self.setPixelHLS(address, color)

        # Fade out
        for address in self._fading_out:
            p, color = self._get_next_color(address, self._fade_out_time, self._current_time + self.parameter('audio-onset-death-boost').get())
            if p >= 1.0:
                self._fading_out.remove(address)
            self.setPixelHLS(address, color)

        # Mass destruction
        if (self._population == self._population_limit) or \
                (self._population > self._mass_destruction_threshold and self._mass_destruction_countdown <= 0):
            for i in self._alive:
                if random.random() > 0.95:
                    self._alive.remove(i)
                    self._dying.append(i)
                    self._population -= 1
            for i in self._growing:
                if random.random() > 0.85:
                    self._growing.remove(i)
                    self._dying.append(i)
                    self._population -= 1
            self._mass_destruction_countdown = self.parameter('mass-destruction-time').get()

    def _get_next_color(self, address, time_target, current_time):
        """
        Returns the next color for a pixel, given the pixel's current state
        """
        progress = (current_time - self._time[address]) / time_target

        if progress > 1.0:
            progress = 1.0
        elif current_time == self._time[address]:
            progress = 0.0

        idx = progress / 3.0
        if time_target == self._death_time:
            idx += (1.0 / 3.0)
        elif time_target == self._fade_out_time:
            idx += (2.0 / 3.0)

        return (progress, self._fader.get_color(idx * self._fader_steps))
