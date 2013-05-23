import logging
from PySide import QtCore, QtNetwork

log = logging.getLogger("firemix.lib.aubio_connector")


class AubioConnector(QtCore.QObject):

    onset_detected = QtCore.Signal()

    PACKET_ONSET = 0x77

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
            if datagram.size() > 0 and ord(datagram[0]) == self.PACKET_ONSET:
                self.onset_detected.emit()