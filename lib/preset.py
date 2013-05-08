import unittest
import time
import logging
import numpy as np

from lib.commands import SetAll, SetStrand, SetFixture, SetPixel

log = logging.getLogger("firemix.lib.preset")


class Preset:
    """Base Preset.  Does nothing."""

    def __init__(self, mixer):
        self._mixer = mixer
        self._commands = []
        self._tickers = []
        self._ticks = 0
        self._parameters = []
        self.setup()

    def reset(self):
        """
        This method is called each time the preset is about to start playing
        """
        self._tickers = []
        self._commands = []
        self._parameters = []
        self.setup()

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
        self._parameters.append(parameter)

    def get_parameters(self):
        return self._parameters

    def parameter(self, key):
        p = None
        for param in self._parameters:
            if str(param) == key:
                p = param
        return p

    def set_parameter(self, key, value):
        """
        Attempts to change the value of a parameter. Returns False if the parameter does not
        exist or the new value is invalid.
        """
        params = [p for p in self._parameters if str(p) == key]
        if len(params) != 1:
            return False
        param = params[0]
        return param.set(value)

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
                log.warn("%s slow frame: %d ms" % (self.__class__, tick_time))

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