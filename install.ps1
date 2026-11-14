# Hive in one line, on Windows (PowerShell):
#   irm https://raw.githubusercontent.com/suryanshranjan/hive/main/install.ps1 | iex
# It installs what Hive needs (Git, Python, Node.js, Claude Code) with winget where missing, then Hive itself in its own
# Python environment (%USERPROFILE%\.hive\venv), puts `hive` on your PATH, and tells you the two things left.
# HIVE_FROM=<pip source> installs Hive from elsewhere; HIVE_HOME moves its folder; HIVE_NO_PATH=1 leaves PATH alone (tests).
$ErrorActionPreference = 'Stop'
function Say($t) { Write-Host $t -ForegroundColor Cyan }
function Have($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Refresh { $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User') }

Say 'Installing Hive'
$need = @()
if (-not (Have git)) { $need += 'Git.Git' }
if (-not (Have python) -and -not (Have py)) { $need += 'Python.Python.3.12' }
if (-not (Have node)) { $need += 'OpenJS.NodeJS.LTS' }
if ($need.Count) {
    if (-not (Have winget)) { Say "Install these first, then run this again: $($need -join ', ') (or get winget from the Microsoft Store: App Installer)"; exit 1 }
    foreach ($id in $need) {
        Say "  Installing $id"
        winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements | Out-Null
    }
    Refresh
}
$py = if (Have py) { 'py' } else { 'python' }
& $py -c 'import sys; sys.exit(sys.version_info < (3, 10))'
if ($LASTEXITCODE) { Say 'Hive needs Python 3.10 or newer.'; exit 1 }
if (-not (Have claude)) { Say '  Installing Claude Code'; npm install -g '@anthropic-ai/claude-code' | Out-Null; Refresh }

Say '  Installing Hive'
$home_ = if ($env:HIVE_HOME) { $env:HIVE_HOME } else { Join-Path $env:USERPROFILE '.hive' }
New-Item -ItemType Directory -Force $home_ | Out-Null
$venv = Join-Path $home_ 'venv'
if (-not (Test-Path (Join-Path $venv 'Scripts\python.exe'))) { & $py -m venv $venv }
$vpy = Join-Path $venv 'Scripts\python.exe'
& $vpy -m pip install -q --upgrade pip | Out-Null
$from = if ($env:HIVE_FROM) { $env:HIVE_FROM } else { 'git+https://github.com/suryanshranjan/hive' }
& $vpy -m pip install -q --upgrade $from
if ($LASTEXITCODE) { Say 'Installing Hive failed (see above).'; exit 1 }
$bin = Join-Path $venv 'Scripts'
if (-not $env:HIVE_NO_PATH) {
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    if (($user -split ';') -notcontains $bin) { [Environment]::SetEnvironmentVariable('Path', "$user;$bin", 'User') }
}
$env:Path = "$env:Path;$bin"

Say ''
Say 'Done: Hive is installed. Two things left, about three minutes:'
Say '  1. claude          (log in to Claude once, then type /exit)'
Say '  2. hive setup      (connects your phone through Telegram; after that, talk to Hive there)'
Say "Open a new terminal first if 'hive' isn't found."
