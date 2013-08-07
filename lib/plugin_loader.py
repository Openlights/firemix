import os
import logging
import inspect

log = logging.getLogger("firemix.lib.plugin_loader")


#TODO: This and PresetLoader share a lot of code...
class PluginLoader:
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