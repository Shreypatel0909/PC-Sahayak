@echo off
rem Removes what PC-Sahayak installed. Asks before deleting your chats, API key or the program folder.
title Uninstall PC-Sahayak
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher\uninstall.ps1"
