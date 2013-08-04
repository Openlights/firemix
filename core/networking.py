import sys
import numpy as np
import socket
import array
import struct
import time

from profilehooks import profile

from lib.colors import hls_to_rgb
from lib.buffer_utils import BufferUtils

COMMAND_SET_BGR = 0x10
COMMAND_SET_RGB = 0x20

class Networking:

    def __init__(self, app):
        self._socket = None
        self._app = app
        self.open_socket()
        self._packet_cache = {}

    def open_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    @profile
    def write(self, buffer):
        """
        Performs a bulk strand write.
        Decodes the HLS-Float data according to client settings
        """
        strand_settings = self._app.scene.get_strand_settings()

        buffer_rgb = hls_to_rgb(buffer) * 255

        def fill_packet(intbuffer, start, end, offset, packet, swap_order=False):
            for pixel_index, pixel in enumerate(intbuffer[start:end]):
                buffer_index = offset + pixel_index * 3
                if swap_order:
                    packet[buffer_index] = pixel[2]
                    packet[buffer_index + 1] = pixel[1]
                    packet[buffer_index + 2] = pixel[0]
                else:
                    packet[buffer_index] = pixel[0]
                    packet[buffer_index + 1] = pixel[1]
                    packet[buffer_index + 2] = pixel[2]

        for client in (client for client in self._app.settings['networking']['clients'] if client["enabled"]):
            # TODO: Split into smaller packets so that less-than-ideal networks will be OK
            client_color_mode = client["color-mode"]
            client_host_port = (client["host"], client["port"])

            for strand in xrange(len(strand_settings)):
                if not strand_settings[strand]["enabled"]:
                    continue
                packet = array.array('B', [])

                color_mode = strand_settings[strand]["color-mode"]
                start, end = BufferUtils.get_strand_extents(strand)

                packet_header_size = 4
                packet_size = (end-start) * 3 + packet_header_size

                packet = self._packet_cache.get(packet_size, None)
                if packet is None:
                    packet = [0,] * packet_size
                    self._packet_cache[packet_size] = packet

                command = COMMAND_SET_RGB if color_mode == "RGB8" else COMMAND_SET_BGR
                packet[0] = strand
                packet[1] = command
                length = packet_size - packet_header_size
                packet[2] = length & 0x00FF
                packet[3] = (length & 0xFF00) >> 8

                # TODO(rryan): Are there other color modes?
                swap_order = client_color_mode == 'BGR8'
                fill_packet(buffer_rgb, start, end, packet_header_size, packet, swap_order)
                packet = array.array('B', packet)

                try:
                    #print "Sending packet of length %i for strand %i", (len(packet), strand)
                    self._socket.sendto(packet, client_host_port)
                except IOError as (errno, strerror):
                    print "I/O error({0}): {1}".format(errno, strerror)
                    #print "On strand %i with length %i" % (strand, len(packet))
                except ValueError:
                    print "Could not convert data to an integer."
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    raise
