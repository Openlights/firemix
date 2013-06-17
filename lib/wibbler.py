import numpy

class Wibbler:
    """
    This manages a value that wanders chaotically within a range
    """
    
    def __init__(self, data):
        self._jerk = data[2]
        self._acceleration = 0
        self._velocity = 0
        self._min = data[0]
        self._max = data[1]
#        print "Wibbler created: ", data

    def update(self, dt, value):
#        print "Wibbler: ", value, self._velocity, self._acceleration
        self._acceleration += (numpy.random.random() - 0.5) * self._jerk * dt
        self._velocity += self._acceleration * dt
        value += self._velocity * dt
        
        _easeFactor = 0.7
        if value + self._velocity * 5 > self._max:
            self._acceleration *= _easeFactor
            self._velocity *= _easeFactor
            
        if value + self._velocity * 5 < self._min:
            self._acceleration *= _easeFactor
            self._velocity *= _easeFactor
            
        if value > self._max:
            self._velocity = 0
            self._acceleration = 0
            value = self._max
        else: 
            if value < self._min:
                self._velocity = 0
                self._acceleration = 0
                value = self._min
        return value        
    