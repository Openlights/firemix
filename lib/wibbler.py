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

import numpy

class Wibbler:
    """
    This manages a value that wanders chaotically within a range
    """
    
    def __init__(self, data):
        self._acceleration = data[2]
        self._velocity = 0
        self._min = data[0]
        self._max = data[1]

    def update(self, dt, value):
        self._velocity += (numpy.random.random() - 0.5) * self._acceleration * dt
        value += self._velocity * dt

        """
        _easeFactor = 0.7
        if value + self._velocity * dt * 10 > self._max:
            self._acceleration *= _easeFactor
            self._velocity *= _easeFactor
            
        if value + self._velocity * dt * 10 < self._min:
            self._acceleration *= _easeFactor
            self._velocity *= _easeFactor
        """
            
        if value > self._max:
            self._velocity = 0
            value = self._max
        elif value < self._min:
            self._velocity = 0
            value = self._min

        return value        
    