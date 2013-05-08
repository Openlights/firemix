import os
import logging

from lib.json_dict import JSONDict
from lib.preset_loader import PresetLoader

log = logging.getLogger("firemix.lib.playlist")


class Playlist(JSONDict):
    """
    Manages the available presets and the current playlist of presets.
    """

    def __init__(self, app):
        self._app = app
        self._name = app.args.playlist
        self._filepath = os.path.join(os.getcwd(), "data", "playlists", "".join([self._name, ".json"]))
        JSONDict.__init__(self, 'playlist', self._filepath, True)

        self._loader = PresetLoader()
        self._preset_classes = self._loader.load()
        self._playlist_data = self.data.get('playlist', [])
        self._playlist = []

        self._active_index = 0
        self._next_index = 0

        self._callback = None

        self.load_playlist()

    def load_playlist(self):
        if len(self._playlist_data) == 0:
            self._playlist = []

        for entry in self._playlist_data:
            inst = self._preset_classes[entry['classname']](self._app.mixer)
            for _, key in enumerate(entry.get('params', {})):
                inst.parameter(key).set(entry['params'][key])
            self._playlist.append(inst)

        self._active_index = 0
        self._next_index = 1 % len(self._playlist)

        return self._playlist

    def register_callback(self, cb):
        self._callback = cb

    def callback(self):
        if self._callback is not None:
            self._callback(self.get_active_preset())

    def get(self):
        return self._playlist

    def advance(self, direction=1):
        """
        Advances the playlist
        """
        self._active_index = (self._active_index + direction) % len(self._playlist)
        self._next_index = (self._next_index + direction) % len(self._playlist)
        self.callback()

    def __len__(self):
        return len(self._playlist)

    def get_active_index(self):
        return self._active_index

    def get_next_index(self):
        return self._next_index

    def get_active_preset(self):
        return self._playlist[self._active_index]

    def get_next_preset(self):
        return self._playlist[self._next_index]

    def get_preset_by_index(self, idx):
        return self._playlist[idx]

    def set_active_index(self, idx):
        self._active_index = idx % len(self._playlist)
        self._next_index = (self._active_index + 1) % len(self._playlist)
        log.info("Setting active index to %d, next index to %d" % (self._active_index, self._next_index))
        self.callback()

    def set_active_preset_by_name(self, classname):
        for i, preset in enumerate(self._playlist):
            if preset.__class__.__name__ == classname:
                self.set_active_index(i)


