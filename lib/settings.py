# This file is part of Firemix.
#
# Copyright 2013-2015 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

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