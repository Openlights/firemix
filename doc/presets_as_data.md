Presets as Data
===============

The idea is to move away from defining presets as code, and towards defining
them as data.  Presets will be broken down into their components, and will be
defined as a pipeline, sort of like GStreamer.

Components are small pieces of Python code that manipulate pixel data.  Each
preset has one or more **components**.

**Transform** components take in pixel location data from Firemix and produce
a modified pixel data array

**Generator** components generate color data using pixel location data (either
from Firemix or from a tranform component)

**Filter** components modify color data from generator components.

Each preset has at least one component defined as an input.  Any "input"
component will be fed data from Firemix.

Each preset has a **pipeline**, which is an ordered list of components.
TODO: Should the list be more than one level deep for parallel pipelines?
The last component in the pipeline must be a generator or filter component,
and its output is used as the preset output.


```
{
    "name": "Test Preset",
    "author": "Jon Evans",
    "allow-playback": true,
    "components": [
        {
            "class": "gradient",
            "name": "gradient-source",
            "parameters": {
                "key1": "value1",
                "key2": "value2"
            }
        },
        {
            "class": "scale",
            "name": "scale-transform",
            "parameters": {
                "key1": "value1",
                "key2": "value2"
            }
        }
    ],
    "sources": [
        "gradient-source"
    ],
    "pipeline": [
        "gradient-source",
        "scale-transform"
    ]
}
```