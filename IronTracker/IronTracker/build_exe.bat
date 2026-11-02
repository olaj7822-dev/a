@echo off
title Iron Project Companion - EXE builder
echo Installing PyInstaller (one time)...
python -m pip install --upgrade pyinstaller keyboard >nul
echo Building IronTracker.exe ...
python -m PyInstaller --onefile --windowed --name IronTracker --clean iron_tracker.py
echo.
echo Done! Your exe is in the "dist" folder: dist\IronTracker.exe
pause
