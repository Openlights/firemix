@echo off
@echo Compiling UI files...
pyside-uic ui/firemix.ui > ui/ui_firemix.py
pyside-uic ui/dlg_add_preset.ui > ui/ui_dlg_add_preset.py
exit
