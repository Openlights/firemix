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


from PySide import QtCore, QtNetwork
import logging
import sys
import signal

logging.basicConfig()
log = logging.getLogger("onset_simulator")


class OnsetSimulator(QtCore.QObject):
    """
    Simulates onset detector for testing without a sound source
    """

    def __init__(self):
        QtCore.QObject.__init__(self)

        self.socket = QtNetwork.QUdpSocket(self)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.send_packet)
        self.timer.start()

    def stop(self):
        self.timer.stop()

    def send_packet(self):
        dgram = QtCore.QByteArray()
        dgram.append(0x77)
        self.socket.writeDatagram(dgram, QtNetwork.QHostAddress.LocalHost, 3010)


def sig_handler(s, f):
    global app
    app.quit()


if __name__ == "__main__":
    log.info("OnsetSimulator starting up")

    app = QtCore.QCoreApplication(sys.argv)
    onset = OnsetSimulator()
    app.aboutToQuit.connect(onset.stop)
    signal.signal(signal.SIGINT, sig_handler)
    sys.exit(app.exec_())
