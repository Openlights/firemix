import os
import json
import logging

log = logging.getLogger("firemix.lib.playlist")


class Playlist:
    """
    Represents a list of presets that is stored long-term in a *.fpl file
    """

    def __init__(self, name=None):
        self._name = name
        self._data = None
        self._filepath = None
        self.load_file()

    def load_file(self):
        """
        Reads JSON data from a *.fpl file
        """
        if self._name is None:
            return False

        self._filepath = os.path.join(os.getcwd(), "data", "playlists", "".join([self._name, ".json"]))

        if not os.path.exists(self._filepath):
            with open(self._filepath, 'w') as f:
                json.dump([], f)
                log.info("Created new playlist at %s", self._filepath)
        else:
            with open(self._filepath, 'r') as f:
                try:
                    raw_data = json.load(f)
                    if raw_data.get('file-type', '') != 'playlist':
                        log.error("Error loading playlist data from %s: file-type mismatch." % self._filepath)
                        self._data = None
                        return None
                    self._data = raw_data.get('playlist', [])
                except:
                    log.error("Error loading playlist data from %s" % self._filepath)
                    self._data = None
                    return None

            log.info("Loaded playlist from %s", self._filepath)
