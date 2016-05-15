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


class Transition:
    """
    Defines the interface for a transition.

    Given two numpy arrays and a progress (0 to 1.0), it produces one output array.
    """

    def __init__(self, app):
        self._app = app

    def __repr__(self):
        """
        Override this with the screen-friendly name of your transition
        """
        return "Transition"

    def setup(self):
        """
        This method will be called once when the transition is loaded
        """
        pass

    def reset(self):
        """
        This method will be called right before the transition is scheduled to start.
        """
        pass

    def get(self, start, end, progress):
        """
        This method will return a frame that is between start and end, according to progress
        """
        pass
