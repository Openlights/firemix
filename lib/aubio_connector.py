import logging
from PySide import QtCore

log = logging.getLogger("firemix.lib.aubio_connector")

AUBIO_AVAILABLE = True
try:
    import aubio
except ImportError:
    AUBIO_AVAILABLE = False


class AubioProcessor(QtCore.QThread):

    audio_data_ready = QtCore.Signal(object)
    beat_detected = QtCore.Signal()

    fft_window = 512
    hop = fft_window / 2
    samplerate = 44100

    def __init__(self):
        QtCore.QThread.__init__(self)
        self._shutdown = False
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.process)
        self._timer.setInterval(10)

        self.sourcename = "/dev/dsp"

        self.source = aubio.source(self.sourcename, self.samplerate, self.hop)
        self.samplerate = self.source.samplerate

        self.onset = aubio.onset("default", self.fft_window, self.hop, self.samplerate)

        log.info("Processing at %d Hz" % self.samplerate)

    @QtCore.Slot()
    def shutdown(self):
        self._shutdown = True

    def run(self):
        self._timer.start()
        self.exec_()
        self._timer.stop()

    def process(self):
        if self._shutdown:
            self.quit()

        samples, read = self.source()
        if read < self.hop:
            log.info("Could not read from audio source.  Shutting down Aubio thread.")
            self.quit()

        self.detect_onset(samples)

    def detect_onset(self, samples):
        if self.onset(samples):
            log.info("onsets detected")
            print "%f" % o.get_last_s()



class AubioConnector(QtCore.QObject):
    """
    Interface to aubio
    """

    def __init__(self):
        QtCore.QObject.__init__(self)

        self._enabled = AUBIO_AVAILABLE
        if not self._enabled:
            log.warn("Aubio could not be loaded.  Audio feature extraction is disabled.")
            return

        self._aubio_processor = AubioProcessor()
        self._aubio_processor.finished.connect(self.on_thread_exit)
        self._aubio_processor.start()


    def on_thread_exit(self):
        log.info("AubioConnector: thread shutdown")

