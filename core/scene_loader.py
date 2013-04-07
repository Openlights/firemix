import unittest
import json
import logging

from lib.scene import Scene

log = logging.getLogger("FireMix.core.SceneLoader")


class SceneLoader:
    """
    Constructs a Scene object from a JSON file
    """

    def __init__(self, filename):
        self._filename = filename
        self._data = None

    def load(self):
        """
        Loads a scene from a JSON file
        """
        assert(self._filename)
        with open(self._filename, 'r') as f:
            try:
                self._data = json.load(f)
            except:
                log.error("Error loading scene data from %s" % self._filename)
                self._data = None
                return None
        self._data["filepath"] = self._filename
        return Scene(self._data)
