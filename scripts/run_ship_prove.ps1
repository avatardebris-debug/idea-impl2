# Controlled ship-prove for Windows (mirrors scripts/run_ship_prove.sh)
# Usage (from factory root):
#   .\scripts\run_ship_prove.ps1
#   .\scripts\run_ship_prove.ps1 -Slug ship_canary -Provider grok -Model grok-4.3
#   .\scripts\run_ship_prove.ps1 -MainPipeline

param(
    [string]$Slug = "",
    [string]$Provider = "",
    [string]$Model = "",
    [switch]$Batch,
    [switch]$WithThermo,
    [switch]$NoClearBus,
    [switch]$MainPipeline,
    [double]$TimeLimit = 0,
    [int]$BaseBudget = 90,
    [int]$PhaseBudget = 45
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

# Load .env
$envFile = Join-Path $Root ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
        if ($_ -match '^([^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

if (-not $Provider) { $Provider = if ($env:PIPELINE_PROVIDER) { $env:PIPELINE_PROVIDER } else { "ollama" } }
if (-not $Model) { $Model = if ($env:PIPELINE_MODEL) { $env:PIPELINE_MODEL } else { "qwen3.6:35b-a3b-q4_K_M" } }

$env:PYTHONUTF8 = "1"
if (-not $env:MAX_FIELD_TEST_LOOPS) { $env:MAX_FIELD_TEST_LOOPS = "2" }
$env:PIPELINE_PROVIDER = $Provider
$env:PIPELINE_MODEL = $Model

$logDir = if ($env:PIPELINE_DIR -and (Test-Path (Join-Path $env:PIPELINE_DIR "logs"))) {
    Join-Path $env:PIPELINE_DIR "logs"
} elseif (Test-Path (Join-Path $Root ".pipeline\logs")) {
    Join-Path $Root ".pipeline\logs"
} else {
    Join-Path $Root "logs"
}
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$mode = if ($MainPipeline) { "main" } else { "ship" }
$logFile = Join-Path $logDir "ship_prove_${mode}_${ts}.log"

Write-Host "run_ship_prove mode=$mode provider=$Provider model=$Model"
Write-Host "log=$logFile"

if (-not $NoClearBus -and -not $MainPipeline) {
    Write-Host "Clearing ship-agent bus..."
    python -c @"
from pipeline.message_bus import MessageBus
from pipeline.pipeline_config import SHIP_AGENT_ROLES
from pipeline.paths import queues_dir, message_bus_db
import sqlite3
bus = MessageBus(queues_dir())
for role in SHIP_AGENT_ROLES:
    n = bus.clear_queue(role)
    print(f'  cleared {role}: {n}')
conn = sqlite3.connect(str(message_bus_db()))
cur = conn.execute(
    'UPDATE messages SET status=? WHERE status=? AND to_agent IN ({})'.format(
        ','.join('?' * len(SHIP_AGENT_ROLES))
    ),
    ['failed', 'processing'] + list(SHIP_AGENT_ROLES),
)
print('  released processing:', cur.rowcount)
conn.commit()
for role in SHIP_AGENT_ROLES:
    print(f'  depth {role}={bus.queue_depth(role)}')
"@
}

if ($MainPipeline) {
    if (-not $env:PIPELINE_POLISH_FIRST) { $env:PIPELINE_POLISH_FIRST = "1" }
    $args = @(
        "pipeline/runner.py", "--from-list",
        "--provider", $Provider, "--model", $Model,
        "--time-limit", "$TimeLimit",
        "--base-budget", "$BaseBudget", "--phase-budget", "$PhaseBudget"
    )
} else {
    $args = @(
        "pipeline/runner.py", "--ship-prove",
        "--provider", $Provider, "--model", $Model,
        "--time-limit", "$TimeLimit",
        "--base-budget", "$BaseBudget", "--phase-budget", "$PhaseBudget"
    )
    if ($Slug) { $args += @("--ship-slug", $Slug) }
    elseif (-not $Batch) { $args += "--ship-serial" }
    if (-not $WithThermo) { $args += "--ship-skip-thermo" }
}

Write-Host ("cmd: python " + ($args -join " "))
python @args 2>&1 | Tee-Object -FilePath $logFile
exit $LASTEXITCODE
