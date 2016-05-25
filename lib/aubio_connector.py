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

import logging
import struct
from PySide import QtCore, QtNetwork

log = logging.getLogger("firemix.lib.aubio_connector")


class AubioConnector(QtCore.QObject):

    onset_detected = QtCore.Signal()
    fft_data = QtCore.Signal(list)
    pitch_data = QtCore.Signal(float, float)

    PACKET_FFT = 0x66
    PACKET_ONSET = 0x77
    PACKET_PITCH = 0x88

    def __init__(self):
        super(AubioConnector, self).__init__()
        self.socket = None
        self.init_socket()

    def init_socket(self):
        self.socket = QtNetwork.QUdpSocket(self)
        self.socket.readyRead.connect(self.read_datagrams)
        self.socket.bind(3010, QtNetwork.QUdpSocket.ShareAddress | QtNetwork.QUdpSocket.ReuseAddressHint)
        log.info("Listening on UDP 3010")

    @QtCore.Slot()
    def read_datagrams(self):
        while self.socket.hasPendingDatagrams():
            datagram = QtCore.QByteArray()
            datagram.resize(self.socket.pendingDatagramSize())
            (datagram, sender, sport) = self.socket.readDatagram(datagram.size())
            if datagram.size() > 0:
                if ord(datagram[0]) == self.PACKET_ONSET:
                    self.onset_detected.emit()
                elif ord(datagram[0]) == self.PACKET_FFT:
                    fft_size = ord(datagram[1]) + (ord(datagram[2]) << 8)
                    fft = []
                    for i in range(fft_size):
                        fft.append(struct.unpack("<f", datagram[3+(i*4):3+(i*4)+4])[0])

                    self.fft_data.emit(fft)
                elif ord(datagram[0]) == self.PACKET_PITCH:
                    pitch = struct.unpack("<f", datagram[1:5])[0]
                    confidence = struct.unpack("<f", datagram[5:9])[0]
                    self.pitch_data.emit(pitch, confidence)
