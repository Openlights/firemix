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

from lib.pattern import Pattern

log = logging.getLogger("firemix.lib.pattern_loader")


class PatternFileEventHandler(PatternMatchingEventHandler):

    patterns = ["*"]
    ignore_directories = False
    callback = None

    def on_created(self, event):
        self.on_modified(event)

    def on_modified(self, event):
        if event.is_directory:
              files_in_dir = [event.src_path+"/"+f for f in os.listdir(event.src_path)]
              if len(files_in_dir) > 0:
                  modified_filename = max(files_in_dir, key=os.path.getmtime)
        else:
            modified_filename = event.src_path
        if modified_filename[-3:] != ".py":
            return
        if self.callback:
            self.callback(modified_filename)


class PatternLoader:
    """
    Scans the ./patterns/ directory and imports all the patterns objects.

    Based on code copyright 2005 Jesse Noller <jnoller@gmail.com>
    http://code.activestate.com/recipes/436873-import-modulesdiscover-methods-from-a-directory-na/
    """

    def __init__(self, parent):
        self._parent = parent
        self._modules = []
        self._patterns = []
        self._patterns_dict = defaultdict()
        self.event_handler = PatternFileEventHandler()
        self.event_handler.callback = self.reload_pattern_by_filename
        self.observer = Observer()
        self.observer.schedule(self.event_handler, os.path.join(os.getcwd(), "patterns"), recursive=True)
        log.info("Watching pattern directory for changes.")
        self.observer.start()

    def __del__(self):
        self.observer.stop()
        self.observer.join()

    def all_patterns(self):
        if not self._patterns_dict:
            self._patterns_dict = self.load()
        return self._patterns_dict

    def load(self):
        self._modules = []
        self._patterns = []
        log.info("Loading patterns...")
        for f in os.listdir(os.path.join(os.getcwd(), "patterns")):
            module_name, ext = os.path.splitext(f)
            if ext == ".py":
                # Skip emacs lock files.
                if f.startswith('.#'):
                    continue

                module = __import__("patterns." + module_name, fromlist=['dummy'])
                self._modules.append(module)
                self._load_patterns_from_modules(module)
        log.info("Loaded %d patterns." % len(self._patterns))
        self._patterns_dict = dict([(klass.__name__, (module, klass)) for module, klass in self._patterns])
        #return dict([(i[1].__name__, i[1]) for i in self._patterns])
        return self._patterns_dict

    def reload(self):
        """Reloads all pattern modules"""
        self._patterns = []
        for module in self._modules:
            reload(module)
            self._load_patterns_from_modules(module)
        #return dict([(i.__name__, i) for i in self._patterns])
        return self._patterns_dict

    def reload_pattern_by_filename(self, filename):
        found = False
        module_file_name = os.path.basename(filename).split('.')[0]
        for idx, module in enumerate(self._modules):
            if module.__name__.split('.')[1] == module_file_name:
                found = True
                log.info("Reloading %s" % filename)
                self._modules[idx] = reload(module)
                self._patterns = [(m, o) for (m, o) in self._patterns if m != module]
                self._load_patterns_from_modules(self._modules[idx])
                self._parent.module_reloaded(module.__name__)

        if not found:
            log.info("Scanning %s for new pattern classes" % filename)
            module = __import__("patterns." + module_file_name, fromlist=['dummy'])
            self._modules.append(module)
            self._load_patterns_from_modules(module)

    def _load_patterns_from_modules(self, module):
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Pattern) and (name is not "Pattern") and (name is not "Pattern"):
                log.info("Loaded %s" % obj.__name__)
                self._patterns.append((module, obj))
                self._patterns_dict[obj.__name__] = (module, obj)



