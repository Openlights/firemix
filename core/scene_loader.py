import os
import logging

from lib.json_dict import JSONDict

log = logging.getLogger("firemix.core.scene_loader")


class SceneLoader(JSONDict):
    """
    Constructs a Scene object from a JSON file
    """

    def __init__(self, app):
        filename = app.args.scene
        self._filename = os.path.join(os.getcwd(), "data", "scenes", "".join([filename, ".json"]))
        JSONDict.__init__(self, 'scene', self._filename, False)
        self.data["filepath"] = self._filename

    def save(self):
        """
        Disable saving for scenes
        """
        pass
