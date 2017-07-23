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

from builtins import object
import os
import logging
import inspect

log = logging.getLogger("firemix.lib.plugin_loader")


#TODO: This and PatternLoader share a lot of code...
class PluginLoader(object):
    """
    Scans the ./plugins/ directory and imports objects into lists based on base class

    Based on code copyright 2005 Jesse Noller <jnoller@gmail.com>
    http://code.activestate.com/recipes/436873-import-modulesdiscover-methods-from-a-directory-na/
    """

    def __init__(self):
        self._classes = {}
        self.load()

    def load(self):
        self._classes = {}
        log.info("Loading plugins...")
        for f in os.listdir(os.path.join(os.getcwd(), "plugins")):
            module_name, ext = os.path.splitext(f)
            if ext == ".py":
                # Skip emacs lock files.
                if f.startswith('.#'):
                    continue

                module = __import__("plugins." + module_name, fromlist=['dummy'])
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    bases = inspect.getmro(obj)
                    if len(bases) > 1:
                        base = bases[1].__name__.rsplit('.',1)[0]
                        if self._classes.get(base, None) is None:
                            self._classes[base] = []
                        self._classes[base].append(obj)
                        log.info("Loaded %s::%s" % (base, obj.__name__))

    def get(self, base):
        return self._classes.get(base, [])
