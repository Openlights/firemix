import unittest


class Fixture:
    """
    Basic model for a fixture
    """

    def __init__(self, data=None):
        self._data = data

    def pixels(self):
        return self._data.get("pixels", 0)

    def pos1(self):
        return tuple(self._data.get("pos1", (0, 0)))

    def pos2(self):
        return tuple(self._data.get("pos2", (0, 0)))

    def midpoint(self):
        p1 = self.pos1()
        p2 = self.pos2()
        return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)