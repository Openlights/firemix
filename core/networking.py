import socket
import array
import struct
from time import sleep


class Networking:

    def __init__(self, app):
        self._socket = None
        self._app = app
        self._clients = [(c["ip"], int(c["port"])) for c in app.settings['networking']['clients']]
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

        # TODO: Split into smaller packets so that less-than-ideal networks will be OK

        for strand in strand_data.keys():
            # Temporary: firmware says #0 is all-call
            # Fixed in FireNode by incrementing strand by one
            #if strand == 0:
            #    continue

            data = strand_data[strand][0:(3*160)]

            length = len(data)
            #packet = array.array('B', [0x27, (length & 0xFF00) >> 8, (length & 0xFF), strand] + strand_data[strand])
            packet = array.array('B', [strand, 0x10, (length & 0xFF), (length & 0xFF00) >> 8] + data)
            for client in self._clients:
                self._socket.sendto(packet, (client[0], client[1]))
            #sleep(0.01)


