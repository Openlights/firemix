import socket
import array
import struct
import colorsys
import time

from lib.colors import clip
from lib.buffer_utils import BufferUtils


COMMAND_SET_BGR = 0x10
COMMAND_SET_RGB = 0x20


class Networking:

    def __init__(self, app):
        self._socket = None
        self._app = app
        self.open_socket()

    def open_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def write(self, buffer):
        """
        Performs a bulk strand write.
        Decodes the HLS-Float data according to client settings
        """
        strand_settings = self._app.scene.get_strand_settings()

        for client in [client for client in self._app.settings['networking']['clients'] if client["enabled"]]:
            # TODO: Split into smaller packets so that less-than-ideal networks will be OK
            packet = array.array('B', [])
            client_color_mode = client["color-mode"]

            for strand in range(len(strand_settings)):
                if not strand_settings[strand]["enabled"]:
                    continue
                color_mode = strand_settings[strand]["color-mode"]

                start, end = BufferUtils.get_strand_extents(strand)
                data = []

                if client_color_mode == "HLSF32":
                    data = [channel for pixel in buffer[start:end] for channel in pixel]
                    data = array.array('B', struct.pack('%sf' % len(data), *data))

                #elif client_color_mode == "HLS16":
                #    data = [int(65535.0 * item) for sublist in buffer for item in sublist]
                #    data = array.array('H', data)

                elif client_color_mode == "RGB8":
                    data = [colorsys.hls_to_rgb(*pixel) for pixel in buffer[start:end]]
                    data = [int(255.0 * item) for sublist in data for item in sublist]
                    data = array.array('B', data)

                elif client_color_mode == "HSVF32":
                    data = [colorsys.hls_to_rgb(*pixel) for pixel in buffer[start:end]]
                    data = array.array('B', [colorsys.rgb_to_hsv(*pixel) for pixel in data])

                length = len(data)
                command = COMMAND_SET_RGB if color_mode == "RGB8" else COMMAND_SET_BGR
                packet.extend(array.array('B', [strand, command, (length & 0xFF), (length & 0xFF00) >> 8]))
                packet.extend(data)


            self._socket.sendto(packet, (client["host"], client["port"]))


