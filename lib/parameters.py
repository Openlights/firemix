


class Parameter:
    """
    Base class for a preset parameter
    """
    def __init__(self, name):
        if not isinstance(name, str):
            raise ValueError("Parameter name must be a string.")
        self._name = name
        self._value = None

    def __repr__(self):
        return self._name

    def get(self):
        return self._value

    def __cmp__(self, other):
        return (self._value == other._value)

    def set(self, value):
        if self.validate(value):
            self._value = value
            return True
        else:
            return False

    def validate(self, value):
        """
        Override this in child classes in order to validate parameter setting
        """
        raise NotImplementedError


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


class RGBParameter(Parameter):
    """
    Parameter holding an RGB tuple (in 8-bit integer)
    """

    def __init__(self, name, value=(0, 0, 0)):
        Parameter.__init__(self, name)
        self.set(value)

    def validate(self, value):
        if not isinstance(value, tuple):
            return False

        if len(value) != 3:
            return False

        if (type(value[0]) != int) or (type(value[1]) != int) or (type(value[2]) != int):
            return False

        if (value[0] < 0 or value[0] > 255) or (value[1] < 0 or value[1] > 255) or (value[2] < 0 or value[2] > 255):
            return False

        return True