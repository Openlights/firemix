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


import os
import logging

from lib.json_dict import JSONDict

log = logging.getLogger("firemix.core.scene_loader")


class SceneLoader(JSONDict):
    """
    Constructs a Scene object from a JSON file
    """

    def __init__(self, app):
        filename = app.args.scene
        self._filename = os.path.join(os.getcwd(), "data", "scenes", "".join([filename, ".json"]))
        JSONDict.__init__(self, 'scene', self._filename, False)
        self.data["filepath"] = self._filename

    def save(self):
        """
        Disable saving for scenes
        """
        pass
