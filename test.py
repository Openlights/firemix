import unittest

import core.mixer
import core.networking

import lib.preset
import lib.basic_tickers
import lib.color_fade


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(lib.color_fade)
    unittest.TextTestRunner(verbosity=2).run(suite)