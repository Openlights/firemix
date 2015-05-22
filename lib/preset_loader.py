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

import os
import logging
import inspect

from lib.preset import Preset

log = logging.getLogger("firemix.lib.preset_loader")


class PresetLoader:
    """
    Scans the ./presets/ directory and imports all the presets objects.

    Based on code copyright 2005 Jesse Noller <jnoller@gmail.com>
    http://code.activestate.com/recipes/436873-import-modulesdiscover-methods-from-a-directory-na/
    """

    def __init__(self):
        self._modules = []
        self._presets = []

    def load(self):
        self._modules = []
        self._presets = []
        log.info("Loading presets...")
        for f in os.listdir(os.path.join(os.getcwd(), "presets")):
            module_name, ext = os.path.splitext(f)
            if ext == ".py":
                # Skip emacs lock files.
                if f.startswith('.#'):
                    continue

                module = __import__("presets." + module_name, fromlist=['dummy'])
                self._modules.append(module)
                self._load_presets_from_modules(module)
        log.info("Loaded %d presets." % len(self._presets))
        return dict([(i.__name__, i) for i in self._presets])

    def reload(self):
        """Reloads all preset modules"""
        self._presets = []
        for module in self._modules:
            reload(module)
            self._load_presets_from_modules(module)
        return dict([(i.__name__, i) for i in self._presets])

    def _load_presets_from_modules(self, module):
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Preset) and (name is not "Preset") and (name is not "RawPreset"):
                log.info("Loaded %s" % obj.__name__)
                self._presets.append(obj)



