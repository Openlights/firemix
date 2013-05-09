import logging
import os

from lib.json_dict import JSONDict

log = logging.getLogger("firemix.lib.settings")


class Settings(JSONDict):

    def __init__(self):
        filepath = os.path.join(os.getcwd(), "data", "settings.json")
        JSONDict.__init__(self, 'settings', filepath, False)

    def save(self):
        JSONDict.save(self)