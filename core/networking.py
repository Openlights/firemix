import socket
import array
import struct
import colorsys
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
        Decodes the HLS-Float data according to client settings
        """
        strand_settings = self._app.scene.get_strand_settings()

        for client in [client for client in self._app.settings['networking']['clients'] if client["enabled"]]:
            # TODO: Split into smaller packets so that less-than-ideal networks will be OK
            packet = array.array('B', [])
            client_color_mode = client["color-mode"]

            for strand in strand_data.keys():
                if not strand_settings[strand]["enabled"]:
                    continue
                color_mode = strand_settings[strand]["color-mode"]

                if client_color_mode == "RGB8":
                    data = [colorsys.hls_to_rgb(*pixel) for pixel in strand_data[strand][0:(3*160)]]
                    data = [int(255.0 * min(1.0, item)) for sublist in data for item in sublist]

                length = len(data)
                command = COMMAND_SET_RGB if color_mode == "RGB8" else COMMAND_SET_BGR
                packet.extend(array.array('B', [strand, command, (length & 0xFF), (length & 0xFF00) >> 8] + data))

            self._socket.sendto(packet, (client["host"], client["port"]))


