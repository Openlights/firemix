import colorsys
import random

from lib.raw_preset import RawPreset
from lib.colors import uint8_to_float, float_to_uint8
from lib.color_fade import ColorFade
from lib.parameters import FloatParameter, IntParameter, RGBParameter


class Dragons(RawPreset):
    """
    Dragons spawn randomly and travel.  At vertices, dragons can reproduce.
    If two dragons collide, both die.
    """

    # Configurable parameters
    _alive_color = (0.01, 1.0, 1.0)  # HSV
    #_tail_color = (0.04, 1.0, 0.5)
    _tail_color = (0.1, 1.0, 0.0)
    _dead_color = (0.1, 0.87, 0.88)  # HSV

    _growth_time = 0.3  # seconds
    _spontaneous_birth_probability = 0.0001

    # Internal parameters
    class Dragon:
        def __init__(self, loc, dir, lifetime):
            self.loc = loc
            self.dir = dir
            self.lifetime = lifetime
            self.growing = True
            self.alive = False
            self.moving = False

        def __repr__(self):
            ds = 'Fwd' if self.dir == 1 else 'Rev'
            return "Dragon (%d, %d, %d) %s: %0.2f" % (self.loc[0], self.loc[1], self.loc[2], ds, self.lifetime)

    _dragons = []
    _tails = []
    _alive_color_rgb = float_to_uint8(colorsys.hsv_to_rgb(*_alive_color))
    _tail_color_rgb = float_to_uint8(colorsys.hsv_to_rgb(*_tail_color))
    _dead_color_rgb = float_to_uint8(colorsys.hsv_to_rgb(*_dead_color))
    _pop = 0

    def setup(self):
        random.seed()
        self.add_parameter(FloatParameter('birth-rate', 0.09))
        self.add_parameter(FloatParameter('tail-persist', 0.55))
        self.add_parameter(IntParameter('pop-limit', 5))
        self._growth_fader = ColorFade('hsv', [(0., 0., 0.), self._alive_color], tick_rate=self._mixer.get_tick_rate())
        self._tail_fader = ColorFade('hsv', [self._alive_color, self._tail_color, (0., 0., 0.)], tick_rate=self._mixer.get_tick_rate())

    def draw(self, dt):

        # Ensure that empty displays start up with some dragons
        p_birth = (1.0 - self._spontaneous_birth_probability) if self._pop > 2 else 0.5

        # Spontaneous birth: Rare after startup
        if (self._pop < self.parameter('pop-limit').get()) and random.random() > p_birth:
            address = ( random.randint(0, self._max_strand - 1),
                        random.randint(0, self._max_fixture - 1),
                        0)
            if address not in [d.loc for d in self._dragons]:
                self._dragons.append(self.Dragon(address, 1, dt))
                self._pop += 1

        # Dragon life cycle
        for dragon in self._dragons:
            # Fade in
            if dragon.growing:
                p = (dt - dragon.lifetime) / self._growth_time
                if (p > 1):
                    p = 1.0
                color = self._growth_fader.get_color(p)
                if p >= 1.0:
                    dragon.growing = False
                    dragon.alive = True
                    dragon.lifetime = dt

                self.setp(dragon.loc, color)

            # Alive - can move or die
            if dragon.alive:
                s, f, p = dragon.loc
                self.setp(dragon.loc, (0, 0, 0))

                # At a vertex: optionally spawn new dragons
                if dragon.moving and  (p == 0 or p == (self.scene().fixture(s, f).pixels - 1)):
                    if (self._pop < self.parameter('pop-limit').get()):
                        neighbors = self.scene().get_pixel_neighbors(dragon.loc)
                        random.shuffle(neighbors)

                        # Iterate over candidate pixels that aren't on the current fixture
                        num_children = 0
                        for candidate in [n for n in neighbors if n[1] != f]:
                            if num_children == 0:
                                # Spawn at least one new dragon to replace the old one.  This first one skips the growth.
                                dir = 1 if candidate[2] == 0 else -1
                                child = self.Dragon(candidate, dir, dt)
                                child.growing = False
                                child.alive = True
                                child.moving = False
                                self._dragons.append(child)
                                self._pop += 1
                                num_children += 1
                            else:
                                # Randomly spawn new dragons
                                if random.random() > (1.0 - self.parameter('birth-rate').get()):
                                    dir = 1 if candidate[2] == 0 else -1
                                    child = self.Dragon(candidate, dir, dt)
                                    child.moving = False

                                    self._dragons.append(child)
                                    self._pop += 1
                                    num_children += 1
                    # Kill dragons that reach the end of a fixture
                    dragon.moving = False
                    self._dragons.remove(dragon)
                    self._pop -= 1
                else:
                    # Move dragons along the fixture
                    self._tails.append((dragon.loc, dt))
                    new_address = (s, f, p + dragon.dir)
                    if new_address[2] < 0 or new_address[2] > 31:
                        print dragon, "new_address", new_address
                        assert(False)
                    dragon.loc = new_address
                    dragon.moving = True
                    self.setp(new_address, self._alive_color_rgb)

                # Kill dragons that run into each other
                if dragon in self._dragons:
                    colliding = [d for d in self._dragons if d != dragon and d.loc == dragon.loc]
                    if len(colliding) > 0:
                        #print "collision between", dragon, "and", colliding[0]
                        self.setp(dragon.loc, (0, 0, 0))
                        self._dragons.remove(dragon)
                        self._dragons.remove(colliding[0])
                        self.setp(dragon.loc, (0, 0, 0))
                        self._pop -= 2

        # Draw tails
        for loc, time in self._tails:
            if (dt - time) > self.parameter('tail-persist').get():
                self._tails.remove((loc, time))
                self.setp(loc, (0, 0, 0))
            else:
                progress = (dt - time) / self.parameter('tail-persist').get()
                self.setp(loc, self._tail_fader.get_color(progress))
