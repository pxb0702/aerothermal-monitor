@echo off
title AeroThermal Monitor (Admin Launcher)
cd /d "%~dp0"
powershell -Command "Start-Process python -ArgumentList 'gui_app.py' -Verb RunAs -WorkingDirectory '%~dp0'"
exit
