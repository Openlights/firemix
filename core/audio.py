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

from __future__ import print_function
from __future__ import division

from past.utils import old_div
import logging
import numpy as np
from scipy import signal

from lib.color_fade import ColorFade

USE_YAPPI = True
try:
    import yappi
except ImportError:
    USE_YAPPI = False

from PyQt5 import QtCore

log = logging.getLogger("firemix.core.mixer")

#curve = [0.1, 0.2, 0.3, 0.6, 0.9, 1.0, 1.0, 1.0, 0.9, 0.6, 0.3, 0.2, 0.1]

class Audio(QtCore.QObject):
    """
    Audio handles looking at sound data and setting it up for use in patterns
    """
    transition_starting = QtCore.pyqtSignal()
    onset = QtCore.pyqtSignal()

    _fader_steps = 256
    SIM_BEATS_PER_MINUTE = 120.0
    SIM_AUTO_ENABLE_DELAY = 3000

    """
    todo zero these at start
    """
    def __init__(self, mixer):
        super(Audio, self).__init__()

        self.mixer = mixer
        self.fft = [[0]]
        self.smoothed = []
        self.average = [[0]]
        self.peak = [[0]]
        self.peakFrequency = [[0]]
        self.gain = 1.0
        self.maxGain = 5.0
        self.fader = ColorFade([(0,0,1), (0,1,1)], self._fader_steps)
        self.pitch = 0.0
        self.pitch_confidence = 0.0

        self.smoothEnergy = 0.0

        self._simulate = False
        self._auto_enable_simulate = False
        self._sim_timer = QtCore.QTimer(self)
        self._sim_timer.setInterval(50)
        self._time_since_last_data = 0
        self._sim_beat = 0
        self._sim_counter = 0
        self._sim_energy = 0.0
        self._sim_fft = []

        self._sim_timer.timeout.connect(self.on_sim_timer)
        self._sim_timer.start()

        self._mutex = QtCore.QMutex()

    def fft_data(self):
        locker = QtCore.QMutexLocker(self._mutex)
        return np.multiply(self.fft, self.gain)

    @QtCore.pyqtSlot()
    def trigger_onset(self):
        self.onset.emit()

    @QtCore.pyqtSlot()
    def on_sim_timer(self):
        dt = self._sim_timer.interval()
        measure = (old_div(60000.0, self.SIM_BEATS_PER_MINUTE))

        if self._simulate:
            if self._auto_enable_simulate and self._time_since_last_data < self.SIM_AUTO_ENABLE_DELAY:
                self._simulate = False
                return

            self._sim_counter += dt
            if self._sim_counter > measure:
                self._sim_counter = 0
                self._sim_beat = 0

            sim_beat_boundary = self._sim_counter % (old_div(measure, 4)) == 0

            if sim_beat_boundary:
                self._sim_beat += 1

            hit = np.random.rand(10) * signal.gaussian(10, 3)

            if self._sim_counter == 0:
                # Kick
                self._sim_energy = 0.5
                hit = np.pad(hit, [0, 246], 'constant', constant_values=0)
                self._sim_fft = hit * self._sim_energy
                self.onset.emit()
            elif self._sim_beat == 2 and sim_beat_boundary:
                # Snare
                self._sim_energy = 0.4
                hit = np.pad(hit, [40, 206], 'constant', constant_values=0)
                self._sim_fft = hit * self._sim_energy
                self.onset.emit()
            else:
                self._sim_energy *= 0.9
                if len(self._sim_fft) == 0:
                    self._sim_fft = np.random.rand(256) * 0.05
                self._sim_fft = self._sim_fft * self._sim_energy

            # Noise floor
            self.update_fft_data(self._sim_fft + (np.random.rand(256) * 0.05))
            QtCore.QMetaObject.invokeMethod(self.mixer._app.gui, "draw_fft")

        else:
            self._time_since_last_data += dt
            if (self._auto_enable_simulate and
                self._time_since_last_data > self.SIM_AUTO_ENABLE_DELAY):
                self._simulate = True
                self.mixer._app.gui.audio_simulate_enabled(True)

    @QtCore.pyqtSlot(int)
    def enable_simulation(self, en):
        self._simulate = (en != 0)

    @QtCore.pyqtSlot(float, float)
    def update_pitch_data(self, pitch, confidence):
        self.pitch = pitch
        self.pitch_confidence = confidence
        #if confidence > 0.9:
        #    print "Pitch: %0.1f" % pitch

    @QtCore.pyqtSlot(list)
    def fft_data_from_network(self, data):
        self._time_since_last_data = 0
        if not self._simulate:
            self.update_fft_data(data)

    def update_fft_data(self, latest_fft):
        if len(latest_fft) == 0:
            print("received no fft")
            return

        latest_fft = np.asarray(latest_fft)

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
            #print "first fft"
            return

        locker = QtCore.QMutexLocker(self._mutex)

        self.peak.insert(0, np.max(latest_fft))
        self.average.insert(0, self.getEnergy())
        self.fft.insert(0, latest_fft)
        self.peakFrequency.insert(0, np.argmax(latest_fft))

        maxPeak = np.max(self.peak)
        if maxPeak > old_div(1, self.maxGain):
            self.gain = old_div(1, maxPeak)
        else:
            self.gain = self.maxGain

        if len(self.fft) > 60:
            self.fft.pop()
            self.peak.pop()
            self.average.pop()
            self.peakFrequency.pop()

            colors = np.zeros((len(self.average), 3))
            colors[:,1] = self.average
            colors[:,0] = np.multiply(self.peakFrequency, old_div(1.0,255))

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
        #self.smoothEnergy = min(1.0, self.smoothEnergy + self.getEnergy())
        self.smoothEnergy = max(self.smoothEnergy, self.getEnergy())

    def getEnergy(self):
        return np.sum(self.fft[0]) / len(self.fft[0]) * self.gain

    def getSmoothEnergy(self):
        return self.smoothEnergy

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

