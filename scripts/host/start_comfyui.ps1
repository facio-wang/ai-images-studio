# AI Images Studio - hidden ComfyUI starter (run by comfyui_launcher.py via the .vbs wrapper)
# Starts ComfyUI with no visible console and records its PID for the one-click stop button.
# NOTE: keep this file ASCII + CRLF.
$ErrorActionPreference = "Stop"

$py = "C:\Program Files\Python311\python.exe"
$workDir = "D:\AI\ComfyUI"
$pyArgs = "main.py --listen 0.0.0.0 --port 8188"

$p = Start-Process -FilePath $py -ArgumentList $pyArgs -WorkingDirectory $workDir -WindowStyle Hidden -PassThru
Set-Content -Path (Join-Path $PSScriptRoot "comfyui.pid") -Value $p.Id -Encoding ascii
