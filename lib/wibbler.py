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
    