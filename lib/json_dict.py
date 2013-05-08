import collections
import json
import os


class JSONDict(collections.MutableMapping):
    """
    Represents a dictionary backed by a JSON file.  The dictionary must contain
    at least one entry, with the key 'file-type' and the value a string passed to __init__().
    This file-type is used for subclasses as a validation step.
    """

    def __init__(self, filetype, filename, create_new):
        self.data = dict()
        self.filetype = filetype
        self.filename = filename
        self._load_from_file(create_new)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def _load_from_file(self, create_new):
        if not os.path.exists(self.filename):
            if create_new:
                with open(self.filename, 'w') as f:
                    json.dump({'file-type': self.filetype}, f)
            else:
                raise ValueError("File %s does not exist." % self.filename)
        else:
            with open(self.filename, 'r') as f:
                try:
                    self.data = json.load(f)
                    if self.data.get('file-type', '') != self.filetype:
                        raise ValueError("Error loading settings from %s: file-type mismatch." % self.filename)
                        self.data = None
                        return None
                except:
                    self.data = None
                    return None

    def _save_to_file(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)
