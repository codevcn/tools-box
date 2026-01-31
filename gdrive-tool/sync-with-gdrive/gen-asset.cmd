@echo off
cd /d "%~dp0"

py scripts/gen_resources.py

if errorlevel 1 (
    echo Error generating resources.
    exit /b 1
)

pyside6-rcc resources.qrc -o app/src/resources_rc.py

if errorlevel 1 (
    echo Error generating resources.
    exit /b 1
)

echo Done to generate resources.