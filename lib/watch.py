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


class Watch:
    """
    Base class for a preset watch (basically a value you can display in the GUI)
    Name must be the name of a member of the preset (parent)
    """
    def __init__(self, parent, name):
        if not isinstance(name, str):
            raise ValueError("Watch name must be a string.")
        self._name = name
        self._parent = parent

    def __repr__(self):
        return self._name

    def get(self):
        return getattr(self._parent, self._name)

    def get_as_str(self):
        return str(self.get())

    def __cmp__(self, other):
        return (self._name == other._name and self._parent == other._parent)
