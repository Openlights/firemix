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
