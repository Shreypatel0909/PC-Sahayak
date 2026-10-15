@echo off
rem Starts PC-Sahayak so phones and other PCs on your local network can use it too (asks first).
title PC-Sahayak (network)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher\start.ps1" -Network
