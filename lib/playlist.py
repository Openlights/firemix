import os
import gc
import logging
import random

from lib.json_dict import JSONDict
from lib.preset_loader import PresetLoader

log = logging.getLogger("firemix.lib.playlist")


class Playlist(JSONDict):
    """
    Manages the available presets and the current playlist of presets.
    """

    def __init__(self, app):
        self._app = app
        self.name = app.args.playlist
        if self.name is None:
            self.name = self._app.settings.get("mixer").get("last_playlist", "default")
        filepath = os.path.join(os.getcwd(), "data", "playlists", "".join([self.name, ".json"]))
        JSONDict.__init__(self, 'playlist', filepath, True)

        self.open()

    def set_filename(self, filename):
        self.name = os.path.split(filename)[1].replace(".json", "")
        self.filename = filename

    def open(self):
        try:
            self.load(False)
        except ValueError:
            print "Error loading %s" % self.filename
            return False

        self._loader = PresetLoader()
        self._preset_classes = self._loader.load()
        self._playlist_data = self.data.get('playlist', [])
        self._playlist = []

        self._active_index = 0
        self._next_index = 0
        self._shuffle = self._app.settings['mixer']['shuffle']
        self._shuffle_list = []

        self.generate_playlist()
        return True

    def generate_playlist(self):
        if len(self._playlist_data) == 0:
            self._playlist = []

        for entry in self._playlist_data:
            if entry['classname'] in self._preset_classes:

                inst = self._preset_classes[entry['classname']](self._app.mixer, name=entry['name'])
                inst._reset()

                for _, key in enumerate(entry.get('params', {})):
                    try:
                        inst.parameter(key).set_from_str(str(entry['params'][key]))
                    except AttributeError:
                        log.warn("Parameter %s called out in playlist but not found in plugin.  Perhaps it was renamed?" % key)
                self._playlist.append(inst)
            else:
                self._playlist_data.remove(entry)

        self._active_index = 0
        if self._shuffle and len(self._playlist) > 1:
            self.generate_shuffle()
            self._next_index = self._shuffle_list.pop()
        else:
            self._next_index = 0 if len(self._playlist) == 0 else 1 % len(self._playlist)

        return self._playlist

    def shuffle_mode(self, shuffle=True):
        """
        Enables or disables playlist shuffle
        """
        self._shuffle = shuffle

    def generate_shuffle(self):
        """
        Creates a shuffle list
        """
        self._shuffle_list = range(len(self._playlist))
        random.shuffle(self._shuffle_list)
        if self._active_index in self._shuffle_list:
            self._shuffle_list.remove(self._active_index)

    def reload_presets(self):
        """Attempts to reload all preset classes in the playlist"""
        old_active = self._active_index
        old_next = self._next_index
        self._preset_classes = self._loader.reload()
        while len(self._playlist) > 0:
            inst = self._playlist.pop(0)
            inst.clear_parameters()
            del inst

        gc.collect()
        self.generate_playlist()
        self._active_index = old_active % len(self._playlist)
        self._next_index = old_next % len(self._playlist)

    def save(self):
        log.info("Saving playlist")
        # Pack the current state into self.data
        self.data = {'file-type': 'playlist'}
        playlist = []
        for preset in self._playlist:
            playlist_entry = {'classname': preset.__class__.__name__,
                              'name': preset.get_name()}
            param_dict = {}
            for name, param in preset.get_parameters().iteritems():
                param_dict[name] = param.get_as_str()
            playlist_entry['params'] = param_dict
            playlist.append(playlist_entry)
        self.data['playlist'] = playlist
        # Superclass write to file
        self._app.settings.get("mixer")["last_playlist"] = self.name
        JSONDict.save(self)

    def get(self):
        return self._playlist

    def advance(self, direction=1):
        """
        Advances the playlist
        """
        #TODO: support transitions other than cut
        self._active_index = self._next_index

        if self._shuffle:
            if len(self._shuffle_list) == 0:
                self.generate_shuffle()
            self._next_index = self._shuffle_list.pop()
        else:
            self._next_index = (self._next_index + direction) % len(self._playlist)

        self._app.playlist_changed.emit()

    def __len__(self):
        return len(self._playlist)

    def get_active_index(self):
        return self._active_index

    def get_next_index(self):
        return self._next_index

    def get_active_preset(self):
        if len(self._playlist) == 0:
            return None
        else:
            return self._playlist[self._active_index]

    def get_preset_relative_to_active(self, pos):
        """
        Returns the preset name of a preset relative to the active preset by an offset of pos
        For exapmle, get_preset_relative_to_active(1) would return the next in the playlist
        """
        return self._playlist[(self._active_index + pos) % len(self._playlist)].get_name()

    def get_next_preset(self):
        if len(self._playlist) == 0:
            return None
        else:
            return self._playlist[self._next_index]

    def get_preset_by_index(self, idx):
        if len(self._playlist) == 0:
            return None
        else:
            return self._playlist[idx]

    def get_preset_by_name(self, name):
        for preset in self._playlist:
            if preset.get_name() == name:
                return preset
        return None

    def set_active_index(self, idx):
        self._active_index = idx % len(self._playlist)
        self._next_index = (self._active_index + 1) % len(self._playlist)
        self.get_active_preset()._reset()
        self._app.playlist_changed.emit()

    def set_active_preset_by_name(self, name):
        #TODO: Support transitions other than jump cut
        for i, preset in enumerate(self._playlist):
            if preset.get_name() == name:
                preset._reset()
                self._active_index = i
                self._app.mixer._elapsed = 0.0  # Hack

    def set_next_preset_by_name(self, name):
        for i, preset in enumerate(self._playlist):
            if preset.get_name() == name:
                self._next_index = i

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
        inst._reset()

        if idx is not None:
            self._playlist.insert(idx, inst)
        else:
            self._playlist.append(inst)

        if self._active_index == self._next_index:
            self._next_index = (self._next_index + 1) % len(self._playlist)

        return True

    def remove_preset(self, name):
        """
        Removes an existing instance from the playlist
        """
        if not self.preset_name_exists(name):
            return False

        pl = [(i, p) for i, p in enumerate(self._playlist) if p.get_name() == name]
        assert len(pl) == 1

        self._playlist.remove(pl[0][1])

        self._next_index = self._next_index % len(self._playlist)
        self._active_index = self._active_index % len(self._playlist)

    def clone_preset(self, old_name):
        old = self.get_preset_by_name(old_name)
        classname = old.__class__.__name__
        new_name = self.suggest_preset_name(classname)
        self.add_preset(classname, new_name)
        new = self.get_preset_by_name(new_name)

        for name, param in old.get_parameters().iteritems():
            new.parameter(name).set_from_str(param.get_as_str())

    def clear_playlist(self):
        self._playlist = []
        self._active_index = 0
        self._next_index = 0

    def rename_preset(self, old_name, new_name):
        pl = [i for i, p in enumerate(self._playlist) if p.get_name() == old_name]
        if len(pl) != 1:
            return False
        self._playlist[pl[0]].set_name(new_name)

    def generate_default_playlist(self):
        """
        Wipes out the existing playlist and adds one instance of each preset
        """
        self.clear_playlist()
        for cn in self._preset_classes:
            name = cn + "-1"
            inst = self._preset_classes[cn](self._app.mixer, name=name)
            inst.setup()
            self._playlist.append(inst)

    def suggest_preset_name(self, classname):
        """
        Returns an unused preset name based on the classname, in the form "Classname-N",
        where N is an integer.
        """
        i = 1
        name = classname + "-" + str(i)
        while self.preset_name_exists(name):
            i += 1
            name = classname + "-" + str(i)
        return name
