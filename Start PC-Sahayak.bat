@echo off
rem Double-click to start PC-Sahayak. It checks what it needs, asks before installing anything, then opens your browser.
title PC-Sahayak
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher\start.ps1" %*
