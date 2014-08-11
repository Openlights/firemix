import unittest
import numpy as np
import logging

from lib.buffer_utils import BufferUtils

log = logging.getLogger('firemix.lib.command')

class Command:
    """
    Base class for all commands
    """
    def __init__(self):
        self._color = (0, 0, 0)
        self._priority = 0
        self._strand = -1
        self._address = -1
        self._pixel = -1

    def __repr__(self):
        strand = self._strand
        address = self._address
        pixel = self._pixel

        return "%s: P%d [%d:%d:%d] (%d, %d, %d)" % (self.__class__, self._priority,
                                                    strand, address, pixel,
                                                    self._color[0], self._color[1], self._color[2])

    def pack(self):
        """
        Returns a serialized version of the command
        """
        pass

    def unpack(self, data):
        """
        Pass in a serialized bytestream to decode it into a command object
        """
        pass

    def get_color(self):
        return self._color

    def get_priority(self):
        return self._priority

    def get_strand(self):
        return self._strand

    def get_address(self):
        return self._address

    def get_pixel(self):
        return self._pixel


class SetAll(Command):
    """
    Sets all pixels to the same color
    """

    def __init__(self, color, priority):
        Command.__init__(self)
        tuple_color = tuple(color)
        if len(tuple_color) != 3:
            raise ValueError("SetAll() expects a 3-tuple for color, got:", color)
        self._color = color
        self._priority = priority

    def pack(self):
        return [0x21, 0x00, 0x03, self._color[0], self._color[1], self._color[2]]

    def unpack(self, data):
        if len(data) != 6:
            raise ValueError("SetAll.unpack() expects 6 data bytes")
        if data[0] != 0x21:
            raise ValueError("SetAll.unpack() received bad data: Command byte incorrect")
        self._color = (data[3], data[4], data[5])
        return self._color


class SetStrand(Command):
    """
    Sets all pixels in a strand to the same color
    """

    def __init__(self, strand, color, priority):
        Command.__init__(self)
        if not isinstance(color, tuple):
            raise ValueError("SetStrand() expects a 3-tuple for color")
        self._strand = strand
        self._color = color
        self._priority = priority

    def pack(self):
        return [0x22, 0x00, 0x04, self._strand, self._color[0], self._color[1], self._color[2]]

    def unpack(self, data):
        if len(data) != 7:
            raise ValueError("SetStrand.unpack() expects 7 data bytes")
        if data[0] != 0x22:
            raise ValueError("SetStrand.unpack() received bad data: Command byte incorrect")
        self._strand = data[3]
        self._color = (data[4], data[5], data[6])
        return (self._strand, self._color)


class SetFixture(Command):
    """
    Sets all pixels in a fixture to the same color
    """

    def __init__(self, strand, address, color, priority):
        Command.__init__(self)
        if not isinstance(color, tuple) and not isinstance(color, np.ndarray):
            raise ValueError("SetFixture() expects a 3-tuple for color")
        self._strand = strand
        self._address = address
        self._color = color
        self._priority = priority

    def pack(self):
        return [0x23, 0x00, 0x05, self._strand, self._address, self._color[0], self._color[1], self._color[2]]

    def unpack(self, data):
        if len(data) != 8:
            raise ValueError("SetFixture.unpack() expects 8 data bytes")
        if data[0] != 0x23:
            raise ValueError("SetFixture.unpack() received bad data: Command byte incorrect")
        self._strand = data[3]
        self._address = data[4]
        self._color = (data[5], data[6], data[7])
        return (self._strand, self._address, self._color)


class SetPixel(Command):
    """
    Sets all pixels in a fixture to the same color
    """

    def __init__(self, strand, address, pixel, color, priority):
        Command.__init__(self)
        if not isinstance(color, tuple):
            raise ValueError("SetPixel() expects a 3-tuple for color")
        self._strand = strand
        self._address = address
        self._pixel = pixel
        self._color = color
        self._priority = priority

    def pack(self):
        return [0x24, 0x00, 0x06, self._strand, self._address, self._pixel, self._color[0], self._color[1], self._color[2]]

    def unpack(self, data):
        if len(data) != 9:
            raise ValueError("SetPixel.unpack() expects 9 data bytes")
        if data[0] != 0x24:
            raise ValueError("SetPixel.unpack() received bad data: Command byte incorrect")
        self._strand = data[3]
        self._address = data[4]
        self._pixel = data[5]
        self._color = (data[6], data[7], data[8])
        return (self._strand, self._address, self._pixel, self._color)


def commands_overlap(first, second):
    """
    Returns True if the two given commands overlap in their output targets (regardless of color)
    """
    if isinstance(first, SetAll) or isinstance(second, SetAll):
        # SetAll will conflict with whatever
        return True

    if isinstance(first, SetStrand) or isinstance(second, SetStrand):
        # By short-circuit above, we know that second will have a _strand attribute
        return (first._strand == second._strand)

    if isinstance(first, SetFixture) or isinstance(second, SetFixture):
        # ditto
        return (first._strand == second._strand and first._address == second._address)

    if isinstance(first, SetPixel) or isinstance(second, SetPixel):
        # ditto
        return (first._strand == second._strand
                and first._address == second._address
                and first._pixel == second._pixel)

    # Oops.  Never should get here unless we add other commands that don't affect output
    return False


def blend_commands(first, second, amount):
    """
    Returns a new command (or list of commands) that is the proportional blend of two inputs.
    Amount is the blend proportion, from 0.0 (100% first) to 1.0 (100% second).

    Example 1: Two SetAll commands would yield a single SetAll with the colors blended
    additively.

    Example 2: A SetAll command and a SetFixture command would yield two commands: The original
    SetAll command with its original priority, and a SetFixture command with a higher priority
    containing the blended color.
    """

def render_command_list(scene, list, buffer):
    """
    Renders the output of a command list to the output buffer.
    Commands are rendered in FIFO overlap style.  Run the list through
    filter_and_sort_commands() beforehand.
    If the output buffer is not zero (black) at a command's target,
    the output will be additively blended according to the blend_state
    (0.0 = 100% original, 1.0 = 100% new)
    """

    for command in list:
        color = command.get_color()
        if isinstance(command, SetAll):
            buffer[:,:] = color

        elif isinstance(command, SetStrand):
            strand = command.get_strand()
            start, end = BufferUtils.get_strand_extents(strand)
            buffer[start:end] = color

        elif isinstance(command, SetFixture):
            strand = command.get_strand()
            address = command.get_address()
            fixture = scene.fixture(strand, address)

            if fixture is None:
                log.error("SetFixture command setting invalid fixture: %s", (strand,address))
                continue

            start = BufferUtils.logical_to_index((strand, address, 0))
            end = start + fixture.pixels
            buffer[start:end] = color

        elif isinstance(command, SetPixel):
            strand = command.get_strand()
            address = command.get_address()
            offset = command.get_pixel()
            pixel = BufferUtils.logical_to_index((strand, address, offset))
            buffer[pixel] = color
