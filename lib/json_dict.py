# This file is part of Firemix.
#
# Copyright 2013-2015 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Firemix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Firemix.  If not, see <http://www.gnu.org/licenses/>.

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
        self.load(create_new)

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

    def load(self, create_new):
        if not os.path.exists(self.filename):
            if create_new:
                with open(self.filename, 'w') as f:
                    json.dump({'file-type': self.filetype}, f)
            else:
                raise ValueError("File %s does not exist." % self.filename)
        else:
            with open(self.filename, 'r') as f:
                try:
                    self.data = self._unicode_to_str(json.load(f))
                    if self.data.get('file-type', None) != self.filetype:
                        raise ValueError("Error loading settings from %s: file-type mismatch." % self.filename)
                except:
                    raise ValueError("Parse error in JSON file.")

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4, sort_keys=True)

    def _unicode_to_str(self, data):
        if isinstance(data, basestring):
            return str(data)
        elif isinstance(data, collections.Mapping):
            return dict(map(self._unicode_to_str, data.iteritems()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(self._unicode_to_str, data))
        else:
            return data
