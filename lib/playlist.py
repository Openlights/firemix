import os
import logging
import inspect

from lib.json_dict import JSONDict
from lib.preset_loader import PresetLoader

log = logging.getLogger("firemix.lib.playlist")


class Playlist(JSONDict):
    """
    Manages the available presets and the current playlist of presets.
    """

    def __init__(self, app):
        self._name = app.args.playlist
        self._filepath = os.path.join(os.getcwd(), "data", "playlists", "".join([self._name, ".json"]))
        JSONDict.__init__(self, 'playlist', self._filepath, True)
        self._loader = PresetLoader()
        self._presets = self._loader.load()

