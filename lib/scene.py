import unittest

from lib.fixture import Fixture


class Scene:
    """
    Basic model for a scene.
    """

    def __init__(self, data):
        self._data = data

    def extents(self):
        return tuple(self._data.get("extents", (0, 0)))

    def name(self):
        return self._data.get("name", "")

    def fixtures(self):
        fl = [Fixture(fd) for fd in self._data["fixtures"]]
