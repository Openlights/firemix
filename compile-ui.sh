#!/bin/bash

if hash pyuic5 2>/dev/null; then
    uic=pyuic5
else
    echo >&2 "Could not find pyuic5!"
    exit 1
fi

$uic ui/firemix.ui > ui/ui_firemix.py
$uic ui/dlg_add_preset.ui > ui/ui_dlg_add_preset.py
$uic ui/dlg_setup_networking.ui > ui/ui_dlg_setup_networking.py
$uic ui/dlg_settings.ui > ui/ui_dlg_settings.py
