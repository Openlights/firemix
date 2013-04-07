import socket
import array
import msgpack


class Networking:

    def __init__(self, ip="127.0.0.1", port=3020):
        self._socket = None
        self._ip = ip
        self._port = port
        self.open_socket()

    def open_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def write(self, data):
        data = [item for sublist in data for item in sublist]
        self._socket.sendto(array.array('B', data), (self._ip, self._port))

    def write_output_buffer(self, output_buffer):
        """
        Performs a bulk write packed with msgpack
        """
        data = msgpack.packb(output_buffer)
        datalen = len(data)
        packet = '\x27' + chr((datalen & 0xFF00) >> 8) + chr(datalen & 0xFF) + data
        self._socket.sendto(packet, (self._ip, self._port))


