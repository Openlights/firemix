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
                module = __import__("presets." + module_name, fromlist=['dummy'])
                self._modules.append(module)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Preset) and (name is not "Preset") and (name is not "RawPreset"):
                        log.info("Loaded %s" % obj.__name__)
                        self._presets.append(obj)
        log.info("Loaded %d presets." % len(self._presets))
        return self._presets



