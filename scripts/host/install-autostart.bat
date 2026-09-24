@echo off
rem ============================================================
rem  AI Images Studio - ComfyUI launcher: register autostart + run now
rem  Writes a VBS into the user Startup folder (pythonw, silent resident)
rem  Uninstall: delete "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ai-studio-comfyui-launcher.vbs"
rem  NOTE: keep this file ASCII + CRLF (cmd.exe parses bat in ANSI codepage).
rem ============================================================
setlocal

set "PYW=C:\Program Files\Python311\pythonw.exe"
set "VBS=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ai-studio-comfyui-launcher.vbs"

if not exist "%PYW%" (
  echo [ERROR] pythonw not found: %PYW%
  echo Edit the PYW path in this script and retry.
  pause
  exit /b 1
)

> "%VBS%" echo Set sh = CreateObject("WScript.Shell")
>>"%VBS%" echo sh.Run """%PYW%"" ""%~dp0comfyui_launcher.py""", 0, False

echo [OK] autostart registered: %VBS%

start "" "%PYW%" "%~dp0comfyui_launcher.py"
echo [OK] launcher running in background, listening on port 8192.
echo Verify: curl http://127.0.0.1:8192/ping
pause
