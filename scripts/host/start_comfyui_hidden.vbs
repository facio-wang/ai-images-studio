' AI Images Studio - hidden ComfyUI launcher wrapper
' Runs start_comfyui.ps1 with NO visible window (wscript, hidden style 0),
' so one-click start never flashes a console that users might close.
' NOTE: keep this file ASCII + CRLF.
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.Run "powershell -NoProfile -ExecutionPolicy Bypass -File """ & dir & "\start_comfyui.ps1""", 0, False
