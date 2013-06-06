import socket
import array
import struct
from time import sleep


COMMAND_SET_BGR = 0x10
COMMAND_SET_RGB = 0x20


class Networking:

    def __init__(self, app):
        self._socket = None
        self._app = app
        self.open_socket()

    def open_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def write(self, data):
        data = [item for sublist in data for item in sublist]
        self._socket.sendto(array.array('B', data), (self._ip, self._port))

    def write_strand(self, strand_data):
        """
        Performs a bulk strand write.
        The expected input format is a dictionary of strand addresses and strand data.
        The input strand data is a flat list of pixel values for all fixtures in the strand.
        Example: {0: [255, 127, 50, 255, 100, 70, ...]}
        """
        strand_settings = self._app.scene.get_strand_settings()

        for client in [client for client in self._app.settings['networking']['clients'] if client["enabled"]]:
            # TODO: Split into smaller packets so that less-than-ideal networks will be OK
            packet = array.array('B', [])

            for strand in strand_data.keys():
                if not strand_settings[strand]["enabled"]:
                    continue
                color_mode = strand_settings[strand]["color-mode"]
                data = strand_data[strand][0:(3*160)]
                length = len(data)
                command = COMMAND_SET_RGB if color_mode == "RGB8" else COMMAND_SET_BGR
                packet.extend(array.array('B', [strand, command, (length & 0xFF), (length & 0xFF00) >> 8] + data))

            self._socket.sendto(packet, (client["host"], client["port"]))


