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


class _Dragon(object):
    def __init__(self, pattern, loc, dir, lifetime):
        self.pattern = pattern
        self.loc = loc
        self.dir = dir
        self.lifetime = lifetime
        self.growing = True
        self.alive = False
        self.growth = 0

    def __repr__(self):
        ds = 'Fwd' if self.dir == 1 else 'Rev'
        return "Dragon %d %s: %0.2f" % (self.loc, ds, self.lifetime)

    def tick(self, dt):
        self.growth += dt * self.pattern.parameter('growth-rate').get()

    def draw(self, to_add, to_remove, population):
        pop_delta = 0

        # Fade in
        if self.growing:
            p = (self.pattern._current_time - self.lifetime) / self.pattern.parameter('growth-time').get()
            if (p > 1):
                p = 1.0
            color = self.pattern._growth_fader.get_color(p * self.pattern._fader_steps)
            if p >= 1.0:
                self.growing = False
                self.alive = True
                self.lifetime = self.pattern._current_time

            self.pattern.setPixelHLS(self.loc, color)

        # Alive - can move or die
        if not self.alive:
            return pop_delta

        for times in range(int(self.growth)):
            s, f, p = BufferUtils.index_to_logical(self.loc)
            self.pattern.setPixelHLS(self.loc, (0, 0, 0))

            if random.random() < self.growth:
                self.growth -= 1

                if ((self.dir == -1 and p == 0)
                    or (self.dir == 1 and p == (self.pattern.scene().fixture(s, f).pixels - 1))):
                    # At a vertex: kill dragons that reach the end of a fixture
                    # and optionally spawn new dragons
                    self.pattern._tails.append((self.loc, self.pattern._current_time, self.pattern._tail_fader))
                    to_remove.add(self)
                    pop_delta -= 1
                    spawned = self._spawn(s, f, population + pop_delta)
                    to_add |= spawned
                    pop_delta += len(spawned)
                    break
                else:
                    # Move dragons along the fixture
                    self.pattern._tails.append((self.loc, self.pattern._current_time, self.pattern._tail_fader))
                    new_address = BufferUtils.logical_to_index((s, f, p + self.dir))
                    self.loc = new_address
                    self.pattern.setPixelHLS(new_address, self.pattern._alive_color)

            # Kill dragons that run into each other
            if self not in to_remove:
                others = (self.pattern._dragons | to_add) - to_remove
                colliding = [d for d in others if d != self and d.loc == self.loc]
                if len(colliding) > 0:
                    #print "collision between", self, "and", colliding[0]
                    to_remove.add(self)
                    pop_delta -= 1
                    for other in colliding:
                        to_remove.add(other)
                        pop_delta -= 1
                    self.pattern._tails.append((self.loc, self.pattern._current_time, self.pattern._explode_fader))
                    neighbors = self.pattern.scene().get_pixel_neighbors(self.loc)
                    for neighbor in neighbors:
                        self.pattern._tails.append((neighbor, self.pattern._current_time, self.pattern._explode_fader))
                    break

        return pop_delta

    def _spawn(self, current_strand, current_fixture, population):
        children = set()
        neighbors = self.pattern.scene().get_pixel_neighbors(self.loc)
        neighbors = [BufferUtils.index_to_logical(n) for n in neighbors]
        random.shuffle(neighbors)

        # Iterate over candidate pixels that aren't on the current fixture
        candidates = [n for n in neighbors
                      if n[:2] != (current_strand, current_fixture)]
        for candidate in candidates:
            child_index = BufferUtils.logical_to_index(candidate)
            if len(children) == 0:
                # Spawn at least one new dragon to replace the old one.  This first one skips the growth.
                dir = 1 if candidate[2] == 0 else -1
                child = _Dragon(self.pattern, child_index, dir, self.pattern._current_time)
                child.growing = False
                child.alive = True
                children.add(child)
                population += 1
            elif (population < self.pattern.parameter('pop-limit').get()
                  and random.random() < self.pattern.parameter('birth-rate').get()):
                # Randomly spawn new dragons
                dir = 1 if candidate[2] == 0 else -1
                child = _Dragon(self.pattern, child_index, dir, self.pattern._current_time)
                children.add(child)
                population +=1

        return children


class Dragons(Pattern):
    """
    Dragons spawn randomly and travel.  At vertices, dragons can reproduce.
    If two dragons collide, both die.
    """

    # Configurable parameters
    _alive_color = (0.0, 1.0, 1.0)
    _tail_color = (0.5, 0.0, 1.0)
    _dead_color = (0.0, 0.0, 0.0)
    _explode_color = (1.0, 1.0, 1.0)
    _fader_steps = 256

    def setup(self):
        self._dragons = set()
        self._tails = []
        self.init_pixels()
        random.seed()
        self._current_time = 0
        self.add_parameter(FloatParameter('growth-time', 2.0))
        self.add_parameter(FloatParameter('birth-rate', 0.4))
        self.add_parameter(FloatParameter('tail-persist', 0.5))
        self.add_parameter(FloatParameter('growth-rate', 1.0))
        self.add_parameter(IntParameter('pop-limit', 20))
        self.add_parameter(HLSParameter('alive-color', self._alive_color))
        self.add_parameter(HLSParameter('dead-color', self._dead_color))
        self.add_parameter(HLSParameter('tail-color', self._tail_color))
        self.add_parameter(HLSParameter('explode-color', self._explode_color))
        self._setup_colors()

    def _setup_colors(self):
        self._alive_color = self.parameter('alive-color').get()
        self._dead_color = self.parameter('dead-color').get()
        self._tail_color = self.parameter('tail-color').get()
        self._explode_color = self.parameter('explode-color').get()
        self._growth_fader = ColorFade([(0., 0., 0.), self._alive_color], self._fader_steps)
        self._tail_fader = ColorFade([self._alive_color, self._tail_color, (0., 0., 0.)], self._fader_steps)
        self._explode_fader = ColorFade([self._explode_color, (0., 0., 0.)], self._fader_steps)

    def parameter_changed(self, parameter):
        self._setup_colors()

    def tick(self, dt):
        super(Dragons, self).tick(dt)
        self._current_time += dt

        for dragon in self._dragons:
            dragon.tick(dt)

    def draw(self):
        # Spontaneous birth: Rare after startup
        if (len(self._dragons) < self.parameter('pop-limit').get()) and random.random() < self.parameter('birth-rate').get():
            strand = random.randint(0, BufferUtils.num_strands - 1)
            fixture = random.randint(0, BufferUtils.strand_num_fixtures(strand) - 1)
            address = BufferUtils.logical_to_index((strand, fixture, 0))
            if address not in [d.loc for d in self._dragons]:
                self._dragons.add(_Dragon(self, address, 1, self._current_time))

        # Dragon life cycle
        to_add = set()
        to_remove = set()
        population = len(self._dragons)
        for dragon in self._dragons:
            population += dragon.draw(to_add, to_remove, population)

        self._dragons = (self._dragons | to_add) - to_remove

        # Draw tails
        tails_to_remove = []
        for loc, time, fader in self._tails:
            if (self._current_time - time) > self.parameter('tail-persist').get():
                if (loc, time, fader) in self._tails:
                    tails_to_remove.append((loc, time, fader))
                self.setPixelHLS(loc, (0, 0, 0))
            else:
                progress = (self._current_time - time) / self.parameter('tail-persist').get()
                self.setPixelHLS(loc, fader.get_color(progress * self._fader_steps))
        for tail in tails_to_remove:
            self._tails.remove(tail)
