FireMix
=======

FireMix is procedural animation system for LED art installations.
Use [FireSim](https://github.com/craftyjon/firesim) to see the output.

[![Build Status](https://travis-ci.org/cdawzrd/firemix.png)](https://travis-ci.org/cdawzrd/firemix)

Installation / Development
--------------------------

Setup instructions are now located on the wiki:
 - [Installation Guide - Windows](https://github.com/Openlights/firemix/wiki/Installation-Guide-(Windows))
 - [Installation Guide - Mac](https://github.com/Openlights/firemix/wiki/Installation-Guide-(Mac))
 - [Installation Guide - Linux](https://github.com/Openlights/firemix/wiki/Installation-Guide-(Linux))

General information and development tips are located on the wiki also,
check out the [main page](https://github.com/craftyjon/firemix/wiki) to get started.


Usage
-----

    python firemix.py demo [--profile] [--playlist listname] [--preset ClassName] [--nogui]

This will start FireMix with the `demo` scene and the default playlist.  The program will
look in the `data/scenes` directory for a file called `demo.json`.

Use the `--playlist` option to specify a playlist name (without extension) to load. The program
will look in the `data/playlists` directory for a file called `listname.json`, and will create
it (as an empty playlist) if it does not exist.

Use the `--profile` option to enable profiling of framerate.
With profiling enabled, a log message will be printed any time a preset takes
more than 30 ms to render a frame.

Use the `--preset` option to specify a preset (by class name) to play forever.
This is useful for preset development.

Use the `--nogui` option to disable the control GUI.

Please send pull requests for new presets and changes/additions to the core!
