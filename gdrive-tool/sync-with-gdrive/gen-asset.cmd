@echo off
cd /d "%~dp0"
pyside6-rcc resources.qrc -o app/src/resources_rc.py
echo Done.