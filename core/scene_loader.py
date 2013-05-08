import unittest
import json
import os
import logging

from lib.scene import Scene

log = logging.getLogger("firemix.core.scene_loader")


class SceneLoader:
    """
    Constructs a Scene object from a JSON file
    """

    def __init__(self, app):
        filename = app.args.scene
        self._filename = os.path.join(os.getcwd(), "data", "scenes", "".join([filename, ".json"]))
        self._data = None

    def load(self):
        """
        Loads a scene from a JSON file
        """
        assert(self._filename)
        with open(self._filename, 'r') as f:
            try:
                self._data = json.load(f)
                if self._data.get('file-type', '') != 'scene':
                    log.error("Error loading scene from %s.  Bad file-type." % self._filename)
                    self._data = None
                    return None
            except:
                log.error("Error loading scene data from %s" % self._filename)
                self._data = None
                return None
        self._data["filepath"] = self._filename

        log.info("Loaded scene from %s", self._filename)
        return Scene(self._data)
