# This file is part of Firemix.
#
# Copyright 2013-2016 Jonathan Evans <jon@craftyjon.com>
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

from collections import defaultdict
import os
import logging
import inspect
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileModifiedEvent, FileDeletedEvent

from lib.preset import Preset

log = logging.getLogger("firemix.lib.preset_loader")


class PresetFileEventHandler(PatternMatchingEventHandler):

    patterns = ["*.py"]
    ignore_directories = True
    callback = None

    def on_modified(self, event):
        if self.callback:
            self.callback(event.src_path)

class PresetLoader:
    """
    Scans the ./presets/ directory and imports all the presets objects.

    Based on code copyright 2005 Jesse Noller <jnoller@gmail.com>
    http://code.activestate.com/recipes/436873-import-modulesdiscover-methods-from-a-directory-na/
    """

    def __init__(self, parent):
        self._parent = parent
        self._modules = []
        self._presets = []
        self._presets_dict = defaultdict()
        self.event_handler = PresetFileEventHandler()
        self.event_handler.callback = self.reload_preset_by_filename
        self.observer = Observer()
        self.observer.schedule(self.event_handler, os.path.join(os.getcwd(), "presets"), recursive=True)
        log.info("Watching preset directory for changes.")
        self.observer.start()

    def __del__(self):
        self.observer.stop()
        self.observer.join()

    def all_presets(self):
        if not self._presets_dict:
            self._presets_dict = self.load()
        return self._presets_dict

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
        self._presets_dict = dict([(classname.__name__, (module, classname)) for module, classname in self._presets])
        return dict([(i[1].__name__, i[1]) for i in self._presets])

    def reload(self):
        """Reloads all preset modules"""
        self._presets = []
        for module in self._modules:
            reload(module)
            self._load_presets_from_modules(module)
        return dict([(i.__name__, i) for i in self._presets])

    def reload_preset_by_filename(self, filename):
        log.info("Reloading %s", filename)
        for idx, module in enumerate(self._modules):
            if module.__name__.split('.')[1] == os.path.basename(filename).split('.')[0]:
                self._modules[idx] = reload(module)
                self._presets = [(m, o) for (m, o) in self._presets if m != module]
                self._load_presets_from_modules(self._modules[idx])
                self._parent.module_reloaded(module.__name__)

    def _load_presets_from_modules(self, module):
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Preset) and (name is not "Preset") and (name is not "Preset"):
                log.info("Loaded %s" % obj.__name__)
                self._presets.append((module, obj))
                self._presets_dict[obj.__name__] = (module, obj)



