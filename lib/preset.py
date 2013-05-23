import unittest
import time
import logging
import numpy as np

from lib.commands import SetAll, SetStrand, SetFixture, SetPixel

log = logging.getLogger("firemix.lib.preset")


class Preset:
    """Base Preset.  Does nothing."""

    def __init__(self, mixer, name=""):
        self._mixer = mixer
        self._commands = []
        self._tickers = []
        self._ticks = 0
        self._parameters = {}
        self._instance_name = name
        self.setup()

    def __repr__(self):
        return "%s (%s)" % (self._instance_name, self.__class__.__name__)

    def set_name(self, name):
        self._instance_name = name

    def get_name(self):
        return self._instance_name

    def reset(self):
        """
        Override this method to perform any initialization that will be triggered
        each time the preset is about to start playing.  Note that code that should
        only run once (e.g. creating parameters) should go in the setup() method instead.
        """
        pass

    def _reset(self):
        self._commands = []
        self.reset()

    def setup(self):
        """
        Override this method to initialize your tickers.
        """
        pass

    def parameter_changed(self, parameter):
        """
        This callback will be called when any parameters are updated.
        """
        pass

    def can_transition(self):
        """
        Override this method to define clear points at which the mixer can
        transition to or from the preset.  By default, the mixer can
        transition at any time.
        """
        return True

    def add_parameter(self, parameter):
        """
        Adds a parameter to the preset (see ./lib/parameters.py)
        """
        parameter.set_parent(self)
        self._parameters[str(parameter)] = parameter

    def get_parameters(self):
        return self._parameters

    def clear_parameters(self):
        self._parameters = []

    def parameter(self, key):
        return self._parameters.get(key, None)

    def set_parameter(self, key, value):
        """
        Attempts to change the value of a parameter. Returns False if the parameter does not
        exist or the new value is invalid.
        """
        try:
            self._parameters[key].set(value)
            return True
        except KeyError:
            return False

    def add_ticker(self, ticker, priority=0):
        """
        Adds a ticker. Tickers are run every tick and can yield any number of
        (lights, color) tuples.

        lights is one of:
            an empty tuple                    (to change all strands)
            a (strand) tuple                  (to change all addresses on the strand)
            a (strand, address) tuple         (to change all pixels on the strand)
            a (strand, address, pixel) tuple  (to change a single pixel)
            a list of any of the above tuples

        color is an (r, g, b) tuple where r, g, and b are either:
            integers between 0 and 255
            floats between 0 and 1

        Tickers get a two arguments: the number of ticks that have
        passed since this preset started, and the approximate amount of time
        this preset has been running for, in seconds.

        The optional priority arguments is used to determine the order in which
        tickers are run. High priorities are run after lower priorities, allowing
        them to override the lower-priority tickers.
        """
        self._tickers.append((ticker, priority))
        # Resort the list here rather than at each tick
        self._tickers = sorted(self._tickers, key=lambda x: x[1])
        return ticker

    def remove_ticker(self, ticker):
        for (t, p) in self._tickers:
            if t == ticker:
                self._tickers.remove((t, p))

    def clear_tickers(self):
        self._tickers = []

    def tick(self):
        if self._mixer._enable_profiling:
            start = time.time()
            # TODO: This does not account for varying frame rate
        dt = self._ticks * (1.0 / self.tick_rate())
        # Assume that self._tickers is already sorted via add_ticker()
        for ticker, priority in self._tickers:
            #b = time.clock()
            for lights, color in ticker(self._ticks, dt):

                if lights is not None:
                    # Made unnecessary by automatic conversion in ColorFade
                    #color = self._convert_color(color)
                    if not isinstance(color, tuple):
                        log.error("Color is not a tuple: %s" % repr(color))

                    if type(lights) == tuple:
                        lights = [lights]

                    for light in lights:
                        if len(light) == 0:
                            self.add_command(SetAll(color, priority))
                        elif len(light) == 1:
                            self.add_command(SetStrand(light[0], color, priority))
                        elif len(light) == 2:
                            self.add_command(SetFixture(light[0], light[1], color, priority))
                        elif len(light) == 3:
                            self.add_command(SetPixel(light[0], light[1], light[2], color, priority))
            #d = 1000.0 * (time.clock() - b)
            #if d > 1:
            #    log.info("took %0.3f ms to render ticker for %s" % (d, self.__class__))
            #    print lights, color

        self._ticks += 1
        if self._mixer._enable_profiling:
            tick_time = 1000.0 * (time.time() - start)
            if tick_time > 30.0:
                log.info("%s slow frame: %d ms" % (self.__class__, tick_time))

    def tick_rate(self):
        return self._mixer.get_tick_rate()

    def clear_commands(self):
        self._commands = []

    def get_commands(self):
        return self._commands

    def get_commands_packed(self):
        return [cmd.pack() for cmd in self._commands]

    def add_command(self, cmd):
        self._commands.append(cmd)

    def _convert_color(self, color):
        if (type(color[0]) == float) or (type(color[1]) == float) or (type(color[2]) == float) or (type(color[1]) ==np.float32):
            return tuple([int(c*255) for c in color])
        else:
            return color

    def scene(self):
        return self._mixer.scene()


class TestPreset(unittest.TestCase):

    pass