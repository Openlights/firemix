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


import logging
import threading
import time
import random
import math
import numpy as np

from lib.color_fade import ColorFade
from profilehooks import profile

USE_YAPPI = True
try:
    import yappi
except ImportError:
    USE_YAPPI = False

from PySide import QtCore

log = logging.getLogger("firemix.core.mixer")

#curve = [0.1, 0.2, 0.3, 0.6, 0.9, 1.0, 1.0, 1.0, 0.9, 0.6, 0.3, 0.2, 0.1]

class Audio(QtCore.QObject):
    """
    Audio handles looking at sound data and setting it up for use in presets
    """
    transition_starting = QtCore.Signal()
    _fader_steps = 256

    """
    todo zero these at start
    """
    def __init__(self, app):
        self.fft = [[0]]
        self.smoothed = []
        self.average = [[0]]
        self.peak = [[0]]
        self.peakFrequency = [[0]]
        self.gain = 1.0
        self.maxGain = 10.0
        self.fader = ColorFade([(0,0,1), (0,1,1)], self._fader_steps)

        self.smoothEnergy = 0.0

    def fft_data(self):
        return np.multiply(self.fft, self.gain)

    def update_fft_data(self, latest_fft):
        if len(latest_fft) == 0:
            print "received no fft"
            return

        #latest_fft = np.asarray(latest_fft)

        # noise_threshold = 0.1
        # np.multiply(latest_fft, 1.0 + noise_threshold, latest_fft)
        # np.maximum(latest_fft - noise_threshold, 0.0, latest_fft)
        #latest_fft = latest_fft * (1.0 + noise_threshold) - noise_threshold

        if len(self.fft[0]) <= 1:
            self.fft[0] = latest_fft
            self.smoothed = np.asarray(latest_fft)
            self.peak[0] = np.max(latest_fft)
            self.peakFrequency[0] = np.argmax(latest_fft)
            self.average[0] = self.getEnergy()
            print "first fft"
            return

        self.peak.insert(0, np.max(latest_fft))
        self.average.insert(0, self.getEnergy())
        self.fft.insert(0, latest_fft)
        self.peakFrequency.insert(0, np.argmax(latest_fft))

        maxPeak = np.max(self.peak)
        if maxPeak > 1 / self.maxGain:
            self.gain = 1 / maxPeak
        else:
            self.gain = self.maxGain

        if len(self.fft) > 60:
            self.fft.pop()
            self.peak.pop()
            self.average.pop()
            self.peakFrequency.pop()

            colors = np.zeros((len(self.average), 3))
            colors[:,1] = self.average
            colors[:,0] = np.multiply(self.peakFrequency, 1.0/255)

            self.fader = ColorFade(colors, self._fader_steps)

#            self.average.pop()
#            averageEnergy = np.sum(self.average) / len(self.fft)

        smoothing = 0.8
        #np.insert(self.smoothed, 0, 0)
        #self.smoothed.pop()
        #self.smoothed *= 0.95 #= np.minimum(self.smoothed - 0.1)
        np.multiply(self.smoothed, 0.97, self.smoothed)
        self.smoothed = np.maximum(self.smoothed, latest_fft, self.smoothed)

        #np.multiply(latest_fft, 1 - smoothing) + np.multiply(self.smoothed, smoothing)

        self.smoothEnergy *= 0.9
        self.smoothEnergy += self.getEnergy()

    def getEnergy(self):
        return np.sum(self.fft[0]) / len(self.fft[0]) * self.gain

    def getLowFrequency(self):
        return self.fft[0][0] * self.gain

    def getHighFrequency(self):
        if len(self.fft[0]) > 1:
            high = self.fft[0][240:]
            return np.sum(high) * self.gain / len(high)
        else:
            return 0

    def getSmoothedFFT(self):
        return np.multiply(self.smoothed, self.gain)

