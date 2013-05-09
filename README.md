FireMix
=======

FireMix is a host for lighting pattern generators--small programs known as "presets".  Use FireSim to see the output.

[![Build Status](https://travis-ci.org/cdawzrd/firemix.png)](https://travis-ci.org/cdawzrd/firemix)

Installation / Development
--------------------------

    pip install -r requirements.txt
    cp data/settings.json.example data/settings.json
    cp data/playlists/default.json.example data/playlists/default.json
    python firemix.py demo [--profile] [--playlist listname] [--preset ClassName] [--nogui]

This will start FireMix with the `demo` scene and the default playlist.  The program will
look in the `data/scenes` directory for a file called `demo.json`.

Use the `--playlist` option to specify a playlist name (without extension) to load. The program
will look in the `data/playlists` directory for a file called `listname.json`, and will create
it (as an empty playlist) if it does not exist.

Use the `--profile` option to enable profiling of framerate and function calls.
With profiling enabled, a log message will be printed any time a preset takes
more than 30 ms to render a frame.

Use the `--preset` option to specify a preset (by class name) to play forever.
This is useful for preset development.

Use the `--nogui` option to disable the control GUI.

Please send pull requests for new presets and changes/additions to the core!
