@echo off
rem AI Images Studio one-click launcher: ComfyUI engine (Win11 host, port 8188)
rem Fired by scripts/host/comfyui_launcher.py -- same as double-clicking this file.
rem NOTE: keep this file ASCII + CRLF (cmd.exe parses bat in ANSI codepage, not UTF-8).
cd /d D:\AI\ComfyUI
"C:\Program Files\Python311\python.exe" main.py --listen 0.0.0.0 --port 8188
