@echo off
title Vein Launcher - Online installer
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-online.ps1" %*
if errorlevel 1 pause
