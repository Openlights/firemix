import socket
import array


class Networking:

    def __init__(self, ip="127.0.0.1", port=3020):
        self._socket = None
        self._ip = ip
        self._port = port
        self.open_socket()

    def open_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def write(self, data):
        #packed = msgpack.packb(data)
        for packet in data:
            self._socket.sendto(array.array('B', packet), (self._ip, self._port))
