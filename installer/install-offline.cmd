@echo off
title Vein Launcher - Offline installer
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-offline.ps1" %*
if errorlevel 1 pause
