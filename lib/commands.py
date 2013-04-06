import unittest


class Command:
    """
    Base class for all commands
    """
    def __init__(self):
        self._color = (0, 0, 0)

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


class SetAll(Command):
    """
    Sets all pixels to the same color
    """

    def __init__(self, color):
        Command.__init__(self)
        if not isinstance(color, tuple):
            raise ValueError("SetAll() expects a 3-tuple for color")
        self._color = color

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

    def __init__(self, strand, color):
        Command.__init__(self)
        if not isinstance(color, tuple):
            raise ValueError("SetStrand() expects a 3-tuple for color")
        self._strand = strand
        self._color = color

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

    def __init__(self, strand, address, color):
        Command.__init__(self)
        if not isinstance(color, tuple):
            raise ValueError("SetFixture() expects a 3-tuple for color")
        self._strand = strand
        self._address = address
        self._color = color

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

    def __init__(self, strand, address, pixel, color):
        Command.__init__(self)
        if not isinstance(color, tuple):
            raise ValueError("SetPixel() expects a 3-tuple for color")
        self._strand = strand
        self._address = address
        self._pixel = pixel
        self._color = color

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