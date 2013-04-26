FireMix
=======

FireMix is a host for lighting pattern generators--small programs known as "presets".  Use FireSim to see the output.

[![Build Status](https://travis-ci.org/cdawzrd/firemix.png)](https://travis-ci.org/cdawzrd/firemix)

Installation / Development
--------------------------

    pip install -r requirements.txt
    python firemix.py [--profile] [--playlist PLIST] demo

Use the `--profile` option to enable profiling of framerate and function calls.
With profiling enabled, a log message will be printed any time a preset takes
more than 12 ms to render a frame.

Use the `--playlist` option to specifiy a playlist name.  If the playlist exists
as a *.fpl file in `data/playlists`, it will be loaded.  If not, it will be created.


Preset Development
------------------

Add your preset to `presets/__init__.py` to include it in the playlist.
Send pull requests with presets!