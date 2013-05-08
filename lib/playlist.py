import os
import logging

from lib.json_dict import JSONDict

log = logging.getLogger("firemix.lib.playlist")


class Playlist(JSONDict):
    """
    Represents a list of presets that is stored long-term in a *.fpl file
    """

    def __init__(self, app):
        self._name = app.args.playlist
        self._filepath = os.path.join(os.getcwd(), "data", "playlists", "".join([self._name, ".json"]))
        JSONDict.__init__(self, 'playlist', self._filepath, True)

