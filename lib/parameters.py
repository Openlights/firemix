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

from builtins import str
from builtins import object
import ast
import numpy
from lib.wibbler import Wibbler

class Parameter(object):
    """
    Base class for a preset parameter
    """
    def __init__(self, name, parent=None):
        if not isinstance(name, str):
            raise ValueError("Parameter name must be a string.")
        self._name = name
        self._value = 0
        self._valueString = None
        self._parent = parent        
        self._wibbler = None

    def tick(self, dt):
        if self._wibbler:
            self._value = self._wibbler.update(dt, self._value)

    def __repr__(self):
        return self._name

    def get(self):
        return self._value

    def get_as_str(self):
        return self._valueString

    def __cmp__(self, other):
        return (self._value == other._value)

    def set(self, value):
        if self.validate(value):
            value = self.normalize(value)
            self._wibbler = None
            self._value = value
            self._valueString = str(value)
            if self._parent is not None and self._parent.initialized:
                self._parent.parameter_changed(self)
            return True
        else:
            return False

    def set_from_str(self, valueString):
        cval = None
        try:
            cval = self._cast_from_str(valueString)
        except ValueError:
            try:
                value = ast.literal_eval(valueString)
                if len(value) == 3:
                    self._wibbler = Wibbler(value)
                    self._value = numpy.random.random() * (self._wibbler._max - self._wibbler._min) + self._wibbler._min
                    self._valueString = valueString
                    if self._parent is not None and self._parent.initialized:
                        self._parent.parameter_changed(self)
                    return True
                return False
            except:
                return False

        if cval is not None:
            return self.set(cval)
        else:
            return False

    def _cast_from_str(self, value):
        """
        Override this in child classes to define how to cast a string into a value
        """
        pass

    def normalize(self, value):
        """
        Override this in child classes to normalize parameter values
        """
        return value

    def validate(self, value):
        """
        Override this in child classes in order to validate parameter setting
        """
        raise NotImplementedError

    def set_parent(self, parent):
        self._parent = parent


class BoolParameter(Parameter):
    """
    Parameter holding a boolean value
    """

    def __init__(self, name, value=False):
        Parameter.__init__(self, name)
        self.set(value)

    def validate(self, value):
        if not isinstance(value, bool):
            return False
        return True

    def _cast_from_str(self, value):
        return True if value == 'True' else False


class StringParameter(Parameter):
    def __init__(self, name, value=""):
        Parameter.__init__(self, name)
        self.set(value)

    def validate(self, value):
        return True

    def _cast_from_str(self, value):
        return str(value)


class IntParameter(Parameter):
    """
    Parameter holding an integer value
    """

    def __init__(self, name, value=0):
        Parameter.__init__(self, name)
        self.set(value)

    def validate(self, value):
        if not isinstance(value, int):
            return False
        return True

    def _cast_from_str(self, value):
        return int(value)


class FloatParameter(Parameter):
    """
    Parameter holding a float value
    """

    def __init__(self, name, value=0.0):
        Parameter.__init__(self, name)
        self.set(value)

    def validate(self, value):
        if not isinstance(value, float):
            return False
        return True

    def _cast_from_str(self, value):
        return float(value)


class FloatTupleParameter(Parameter):
    """
    Parameter holding a float value
    """

    def __init__(self, name, size, value=None):
        Parameter.__init__(self, name)
        self.size = size
        if (value is not None):
            self.set(value)
        else:
            self.set(tuple([0.] * self.size))

    def validate(self, value):
        if not isinstance(value, tuple):
            return False
        if (len(value) != self.size):
            return False
        for item in value:
            if not isinstance(item, float):
                return False
        return True

    def _cast_from_str(self, value):
        return tuple(ast.literal_eval(value))


class RGBParameter(Parameter):
    """
    Parameter holding an RGB tuple (in 8-bit integer)
    """

    def __init__(self, name, value=(0, 0, 0)):
        Parameter.__init__(self, name)
        self.set(tuple(value))

    def normalize(self, value):
        return tuple(value)

    def validate(self, value):
        if (not isinstance(value, tuple)) and (not isinstance(value, list)):
            return False

        if len(value) != 3:
            return False

        if (type(value[0]) != int) or (type(value[1]) != int) or (type(value[2]) != int):
            return False

        if (value[0] < 0 or value[0] > 255) or (value[1] < 0 or value[1] > 255) or (value[2] < 0 or value[2] > 255):
            return False

        return True

    def _cast_from_str(self, value):
        return ast.literal_eval(value)


class HSVParameter(Parameter):
    """
    Parameter holding an HSV tuple (in normalized floating-point)
    """

    def __init__(self, name, value=(0., 0., 0.)):
        Parameter.__init__(self, name)
        self.set(tuple(value))

    def normalize(self, value):
        return tuple(value)

    def validate(self, value):
        if (not isinstance(value, tuple)) and (not isinstance(value, list)):
            return False

        if len(value) != 3:
            return False

        if (type(value[0]) != float) or (type(value[1]) != float) or (type(value[2]) != float):
            return False

        if (value[0] < 0. or value[0] > 1.) or (value[1] < 0. or value[1] > 1.) or (value[2] < 0. or value[2] > 1.):
            return False

        return True

class HLSParameter(Parameter):
    """
    Parameter holding an HSV tuple (in normalized floating-point)
    """

    def __init__(self, name, value=(0., 0., 0.)):
        Parameter.__init__(self, name)
        self.set(tuple(value))

    def normalize(self, value):
        return tuple(value)

    def validate(self, value):
        if (not isinstance(value, tuple)) and (not isinstance(value, list)):
            return False

        if len(value) != 3:
            return False

        return True

    def _cast_from_str(self, value):
        return ast.literal_eval(value)
