import colorsys
import random

from lib.raw_preset import RawPreset
from lib.colors import uint8_to_float, float_to_uint8
from lib.color_fade import ColorFade
from lib.parameters import FloatParameter, IntParameter, HLSParameter


class Dragons(RawPreset):
    """
    Dragons spawn randomly and travel.  At vertices, dragons can reproduce.
    If two dragons collide, both die.
    """

    # Configurable parameters
    _alive_color = (0.0, 1.0, 1.0)
    _tail_color = (0.5, 0.0, 1.0)
    _dead_color = (0.0, 0.0, 0.0)
    _explode_color = (1.0, 1.0, 1.0)

    # Internal parameters
    class Dragon:
        def __init__(self, loc, dir, lifetime):
            self.loc = loc
            self.dir = dir
            self.lifetime = lifetime
            self.growing = True
            self.alive = False
            self.moving = False
            self.growth = 0

        def __repr__(self):
            ds = 'Fwd' if self.dir == 1 else 'Rev'
            return "Dragon (%d, %d, %d) %s: %0.2f" % (self.loc[0], self.loc[1], self.loc[2], ds, self.lifetime)

    def setup(self):
        self._dragons = []
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
        self._growth_fader = ColorFade([(0., 0., 0.), self._alive_color], tick_rate=self._mixer.get_tick_rate())
        self._tail_fader = ColorFade([self._alive_color, self._tail_color, (0., 0., 0.)], tick_rate=self._mixer.get_tick_rate())
        self._explode_fader = ColorFade([self._explode_color, (0., 0., 0.)], tick_rate=self._mixer.get_tick_rate())

    def parameter_changed(self, parameter):
        self._setup_colors()

    def draw(self, dt):

        self._current_time += dt
        
        # Spontaneous birth: Rare after startup
        if (len(self._dragons) < self.parameter('pop-limit').get()) and random.random() < self.parameter('birth-rate').get():
            address = ( random.randint(0, self._max_strand - 1),
                        random.randint(0, self._max_fixture - 1),
                        0)
            if address not in [d.loc for d in self._dragons]:
                self._dragons.append(self.Dragon(address, 1, self._current_time))

        growth_rate = self.parameter('growth-rate').get()
        
        # Dragon life cycle
        for dragon in self._dragons:
            # Fade in
            if dragon.growing:
                p = (self._current_time - dragon.lifetime) / self.parameter('growth-time').get()
                if (p > 1):
                    p = 1.0
                color = self._growth_fader.get_color(p)
                if p >= 1.0:
                    dragon.growing = False
                    dragon.alive = True
                    dragon.lifetime = self._current_time

                self.setPixelHLS(dragon.loc, color)

            # Alive - can move or die
            if dragon.alive:

                dragon.growth += dt * growth_rate
                for times in range(int(dragon.growth)):
                    s, f, p = dragon.loc
                    self.setPixelHLS(dragon.loc, (0, 0, 0))

                    if random.random() < dragon.growth:
                        dragon.growth -= 1
                    
                        # At a vertex: optionally spawn new dragons
                        if dragon.moving and (p == 0 or p == (self.scene().fixture(s, f).pixels - 1)):
                            neighbors = self.scene().get_pixel_neighbors(dragon.loc)
                            random.shuffle(neighbors)

                            # Kill dragons that reach the end of a fixture
                            dragon.moving = False
                            if dragon in self._dragons:
                                self._dragons.remove(dragon)
                                
                            # Iterate over candidate pixels that aren't on the current fixture
                            num_children = 0
                            for candidate in [n for n in neighbors if n[1] != f]:
                                if num_children == 0:
                                    # Spawn at least one new dragon to replace the old one.  This first one skips the growth.
                                    dir = 1 if candidate[2] == 0 else -1
                                    child = self.Dragon(candidate, dir, self._current_time)
                                    child.growing = False
                                    child.alive = True
                                    child.moving = False
                                    self._dragons.append(child)
                                    num_children += 1
                                elif (len(self._dragons) < self.parameter('pop-limit').get()):
                                    # Randomly spawn new dragons
                                    if random.random() < self.parameter('birth-rate').get():
                                        dir = 1 if candidate[2] == 0 else -1
                                        child = self.Dragon(candidate, dir, self._current_time)
                                        child.moving = False

                                        self._dragons.append(child)
                                        num_children += 1
                            break;
                        else:
                            # Move dragons along the fixture
                            self._tails.append((dragon.loc, self._current_time, self._tail_fader))
                            new_address = (s, f, p + dragon.dir)
                            if new_address[2] < 0 or new_address[2] > 31:
                                print dragon, "new_address", new_address
                                assert(False)
                            dragon.loc = new_address
                            dragon.moving = True
                            self.setPixelHLS(new_address, self._alive_color)

                    # Kill dragons that run into each other
                    if dragon in self._dragons:
                        colliding = [d for d in self._dragons if d != dragon and d.loc == dragon.loc]
                        if len(colliding) > 0:
                            #print "collision between", dragon, "and", colliding[0]
                            self._dragons.remove(dragon)
                            self._dragons.remove(colliding[0])
                            self._tails.append((dragon.loc, self._current_time, self._explode_fader))
                            neighbors = self.scene().get_pixel_neighbors(dragon.loc)
                            for neighbor in neighbors:
                                self._tails.append((neighbor, self._current_time, self._explode_fader))
                            break

        # Draw tails
        for loc, time, fader in self._tails:
            if (self._current_time - time) > self.parameter('tail-persist').get():
                self._tails.remove((loc, time, fader))
                self.setPixelHLS(loc, (0, 0, 0))
            else:
                progress = (self._current_time - time) / self.parameter('tail-persist').get()
                self.setPixelHLS(loc, fader.get_color(progress))