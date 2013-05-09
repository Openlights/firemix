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

        self.generate_playlist()

    def generate_playlist(self):
        if len(self._playlist_data) == 0:
            self._playlist = []

        for entry in self._playlist_data:
            inst = self._preset_classes[entry['classname']](self._app.mixer, name=entry['name'])
            for _, key in enumerate(entry.get('params', {})):
                inst.parameter(key).set(entry['params'][key])
            self._playlist.append(inst)

        self._active_index = 0
        self._next_index = 1 % len(self._playlist)

        return self._playlist

    def save(self):
        log.info("Saving playlist")
        # Pack the current state into self.data
        self.data = {'file-type': 'playlist'}
        playlist = []
        for preset in self._playlist:
            playlist_entry = {'classname': preset.__class__.__name__,
                              'name': preset.get_name()}
            param_dict = {}
            for param in preset.get_parameters():
                param_dict[str(param)] = param.get()
            playlist_entry['params'] = param_dict
            playlist.append(playlist_entry)
        self.data['playlist'] = playlist
        # Superclass write to file
        JSONDict.save(self)

    def get(self):
        return self._playlist

    def advance(self, direction=1):
        """
        Advances the playlist
        """
        self._active_index = (self._active_index + direction) % len(self._playlist)
        self._next_index = (self._next_index + direction) % len(self._playlist)
        self._app.playlist_changed.emit()

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
        self.get_active_preset()._reset()
        self._app.playlist_changed.emit()

    def set_active_preset_by_name(self, classname):
        for i, preset in enumerate(self._playlist):
            if preset.get_name() == classname:
                self.set_active_index(i)

    def reorder_playlist_by_names(self, names):
        """
        Pass in a list of preset names to reorder.
        """
        current = dict([(preset.get_name(), preset) for preset in self._playlist])

        new = []
        for name in names:
            new.append(current[name])

        self._playlist = new

    def get_available_presets(self):
        return self._preset_classes.keys()

    def preset_name_exists(self, name):
        return True if name in [p.get_name() for p in self._playlist] else False

    def add_preset(self, classname, name, idx=None):
        """
        Adds a new preset instance to the playlist.  Classname must be a currently loaded
        preset class.  Name must be unique.  If idx is specified, the preset will be inserted
        at the position idx, else it will be appended to the end of the playlist.
        """
        if classname not in self._preset_classes:
            log.error("Tried to add nonexistent preset class %s" % classname)
            return False

        if self.preset_name_exists(name):
            return False

        inst = self._preset_classes[classname](self._app.mixer, name=name)

        if idx is not None:
            self._playlist.insert(idx, inst)
        else:
            self._playlist.append(inst)
        return True

    def remove_preset(self, name):
        """
        Removes an existing instance from the playlist
        """
        if not self.preset_name_exists(name):
            return False

        pl = [p for p in self._playlist if p.get_name() == name]
        assert len(pl) == 1
        self._playlist.remove(pl[0])

    def clear_playlist(self):
        self._playlist = []

