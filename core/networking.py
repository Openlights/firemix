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
        data = [item for sublist in data for item in sublist]
        self._socket.sendto(array.array('B', data), (self._ip, self._port))
