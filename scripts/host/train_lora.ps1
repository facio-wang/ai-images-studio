# AI Images Studio - LoRA training launcher (host side). ASCII + CRLF only.
# Reads scripts/host/train_config.json and runs the configured command hidden via cmd,
# replacing {dataset} {trigger} {workdir} placeholders. stdout+stderr are merged into
# <repo>/data/lora_train/<dataset>.log ; the process PID is written to
# scripts/host/lora_train_<dataset>.pid (used by comfyui_launcher.py /train/stop).
#
# train_config.json example:
#   { "command": "python", "argsTemplate": "train.py --dataset {dataset} --trigger {trigger}" }
param(
    [Parameter(Mandatory=$true)][string]$Dataset,
    [Parameter(Mandatory=$true)][string]$Trigger
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$cfgPath = Join-Path $scriptDir "train_config.json"
$workdir = "D:\AI\sd-train"
if (-not (Test-Path $workdir)) { $workdir = $scriptDir }
$logDir = Join-Path $repoRoot "data\lora_train"
$logPath = Join-Path $logDir ($Dataset + ".log")
$pidPath = Join-Path $scriptDir ("lora_train_" + $Dataset + ".pid")

if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Write-TrainLog([string]$line) {
    $stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $logPath -Value ("[" + $stamp + "] " + $line)
}

if (-not (Test-Path $cfgPath)) {
    Write-TrainLog ("train_config.json not found: " + $cfgPath)
    exit 1
}

$cfg = $null
try {
    $cfg = Get-Content -Path $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
} catch {
    Write-TrainLog ("train_config.json is not valid JSON: " + $_.Exception.Message)
    exit 1
}

$command = ""
$argsTemplate = ""
if ($cfg -ne $null) {
    if ($cfg.command -ne $null) { $command = [string]$cfg.command }
    if ($cfg.argsTemplate -ne $null) { $argsTemplate = [string]$cfg.argsTemplate }
}

if ([string]::IsNullOrWhiteSpace($command)) {
    Write-TrainLog 'Training command is NOT configured. Please edit scripts/host/train_config.json and fill in the training entry from your old project. Placeholders: {dataset} {trigger} {workdir}. Example: {"command": "python", "argsTemplate": "train.py --dataset {dataset} --trigger {trigger} --output {workdir}\{dataset}"}'
    exit 1
}

$full = ($command + " " + $argsTemplate)
$full = $full.Replace("{dataset}", $Dataset).Replace("{trigger}", $Trigger).Replace("{workdir}", $workdir)

Write-TrainLog ("start: " + $full)

try {
    # cmd /c keeps shell semantics (quotes / env vars); >> merges stdout+stderr into one log
    $cmdline = "/c " + $full + " >> `"$logPath`" 2>&1"
    $p = Start-Process -FilePath "cmd.exe" -ArgumentList $cmdline -WorkingDirectory $workdir -WindowStyle Hidden -PassThru
    Set-Content -Path $pidPath -Value $p.Id -Encoding Ascii
    Write-TrainLog ("started, pid=" + $p.Id)
} catch {
    Write-TrainLog ("failed to start: " + $_.Exception.Message)
    exit 1
}
