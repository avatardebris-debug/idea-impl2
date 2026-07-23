# P0: Overnight-hardened Grok Build from-list (Windows)
# Freezes env, preflights, runs serial runner, then morning report + optional extract.
#
# Usage (from factory repo root):
#   .\scripts\overnight_grok_from_list.ps1
#   .\scripts\overnight_grok_from_list.ps1 -TimeLimitMinutes 30
#   .\scripts\overnight_grok_from_list.ps1 -TimeLimitMinutes 480
#   .\scripts\overnight_grok_from_list.ps1 -DoExtract          # cloud zip
#   .\scripts\overnight_grok_from_list.ps1 -NoFreshListOnly    # also resume old in-flight
#
# REQUIREMENTS:
#   - Host must stay awake (disable sleep on AC)
#   - Do not run concurrent bulk_thin_field_ship
#   - LOCAL default: --provider grok + GROK_BUILD_CMD; no extract zip
#   - CLOUD/Vast: -Provider ollama -Model <tag> -DoExtract

param(
    [string]$PipelineDir = "C:\Users\avata\aicompete\thepipeline",
    [string]$FactoryRoot = "",
    [double]$TimeLimitMinutes = 480,
    [string]$Provider = "grok",
    [string]$Model = "",
    [string]$IdeasFile = "",
    # Local default: no zip. Cloud sync: pass -DoExtract.
    [switch]$DoExtract,
    [switch]$DryRunEnvOnly,
    # Default ON (--fresh-list-only): new seeds only, not classic backlog zombies.
    [switch]$NoFreshListOnly
)

$ErrorActionPreference = "Stop"

if (-not $FactoryRoot) {
    $FactoryRoot = Split-Path -Parent $PSScriptRoot
    if (-not (Test-Path (Join-Path $FactoryRoot "pipeline\runner.py"))) {
        $FactoryRoot = "C:\Users\avata\.grok\worktrees\aicompete-idea-impl\idea-impl2"
    }
}

# Load factory .env into this process (do not override already-set vars; never print secrets)
function Import-DotEnvFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return 0 }
    $n = 0
    Get-Content -Path $Path -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        if ($line -match '^\s*export\s+') { $line = $line -replace '^\s*export\s+', '' }
        $eq = $line.IndexOf("=")
        if ($eq -lt 1) { return }
        $key = $line.Substring(0, $eq).Trim()
        $val = $line.Substring($eq + 1).Trim()
        if ($val.Length -ge 2) {
            $q = $val[0]
            if (($q -eq [char]34 -or $q -eq [char]39) -and $val[-1] -eq $q) {
                $val = $val.Substring(1, $val.Length - 2)
            }
        }
        # Skip junk lines that are not KEY=value (e.g. bare "GROK_BUILD_CMD" or PowerShell)
        if ($key -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') { return }
        if ($val -match '^\$env:') { return }
        $existing = [Environment]::GetEnvironmentVariable($key, "Process")
        if ([string]::IsNullOrEmpty($existing)) {
            [Environment]::SetEnvironmentVariable($key, $val, "Process")
            $n++
        }
    }
    return $n
}

$envLoaded = 0
$envLoaded += Import-DotEnvFile (Join-Path $FactoryRoot ".env")
$envLoaded += Import-DotEnvFile (Join-Path $PipelineDir ".env")

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir = Join-Path $PipelineDir "logs\overnight_$ts"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$runnerLog = Join-Path $logDir "runner.log"
$preflightLog = Join-Path $logDir "preflight.json"

# --- Env contract (process-local; freeze overnight knobs) ---
$env:PIPELINE_DIR = $PipelineDir
$env:PIPELINE_ENGINE = "grok_build"
$env:GROK_BUILD_BACKEND = "cli"
$env:GROK_BUILD_DRY_RUN = "0"
$env:GROK_BUILD_TIMEOUT_S = if ($env:GROK_BUILD_TIMEOUT_S) { $env:GROK_BUILD_TIMEOUT_S } else { "1800" }
$env:GROK_BUILD_THIN_SHIP = "1"
$env:GROK_BUILD_PLAN_SKILLS = "1"
$env:FIELD_SHIP_REPAIR = "1"
$env:FIELD_SHIP_REPAIR_BACKEND = "cli"
$env:PIPELINE_GROK_SIDECAR = "0"
$env:PYTHONUNBUFFERED = "1"

if (-not $env:GROK_BUILD_CMD) {
    $env:GROK_BUILD_CMD = 'C:\Users\avata\.grok\bin\grok.exe --cwd "{workspace}" --prompt-file "{prompt_file}" --always-approve --max-turns 40 --output-format plain'
}

# Model defaults by provider (local Grok API vs cloud Ollama)
if (-not $Model) {
    if ($Provider -eq "ollama") {
        $Model = if ($env:PIPELINE_MODEL -and $env:PIPELINE_MODEL -notmatch "grok") {
            $env:PIPELINE_MODEL
        } else { "" }  # resolve from ollama list below
    } else {
        # grok / openai / etc. — use .env PIPELINE_MODEL when it is an API model
        $Model = if ($env:PIPELINE_MODEL) { $env:PIPELINE_MODEL } else { "grok-4.3" }
    }
}

$preferredOllamaModels = @(
    $(if ($env:PIPELINE_MODEL -and $env:PIPELINE_MODEL -notmatch "grok") { $env:PIPELINE_MODEL } else { $null }),
    "qwen3.6:35b-a3b-q4_K_M",
    "qwen3.6:35b",
    "gemma4:latest",
    "gemma4",
    "llama3.2:latest"
) | Where-Object { $_ }

$pre = [ordered]@{
    ts             = (Get-Date -Format o)
    pipeline_dir   = $PipelineDir
    factory_root   = $FactoryRoot
    time_limit_min = $TimeLimitMinutes
    provider       = $Provider
    model          = $Model
    grok_cmd_set   = [bool]$env:GROK_BUILD_CMD
    engine         = $env:PIPELINE_ENGINE
    backend        = $env:GROK_BUILD_BACKEND
    thin_ship      = $env:GROK_BUILD_THIN_SHIP
    plan_skills    = $env:GROK_BUILD_PLAN_SKILLS
    fresh_list_only = (-not $NoFreshListOnly)
    dotenv_keys    = $envLoaded
    xai_key_set    = [bool]($env:XAI_API_KEY -or $env:GROK_API_KEY)
    ollama_models  = @()
    errors         = @()
    warnings       = @()
}

# Field rework caps (accumulative; not infinite token/time on stuck ship projects)
if (-not $env:FIELD_REWORK_MAX_ATTEMPTS) { $env:FIELD_REWORK_MAX_ATTEMPTS = "3" }
if (-not $env:FIELD_REWORK_MAX_MINUTES) { $env:FIELD_REWORK_MAX_MINUTES = "45" }
# Cross-model budget (API tokens or agent_timing tokens; Grok CLI ~char/4 fallback)
if (-not $env:FIELD_REWORK_MAX_TOKENS) { $env:FIELD_REWORK_MAX_TOKENS = "2500000" }

# --- Preflight ---
if (-not (Test-Path (Join-Path $PipelineDir "projects"))) {
    $pre.errors += "PIPELINE_DIR/projects missing: $PipelineDir"
}
$grokExe = "C:\Users\avata\.grok\bin\grok.exe"
if (-not (Test-Path $grokExe)) {
    $pre.errors += "grok.exe not found: $grokExe"
}
if (-not $env:GROK_BUILD_CMD) {
    $pre.errors += "GROK_BUILD_CMD empty"
}

# Provider-specific preflight
if ($Provider -eq "ollama") {
    # Cloud/local Ollama: model must be pulled
    try {
        $tagsJson = & ollama list 2>$null
        try {
            $api = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
            $available = @($api.models | ForEach-Object { $_.name })
        } catch {
            $available = @()
            if ($tagsJson) {
                $available = @($tagsJson | Select-Object -Skip 1 | ForEach-Object {
                    ($_ -split '\s+')[0]
                } | Where-Object { $_ })
            }
        }
        $pre.ollama_models = $available
        if ($available.Count -eq 0) {
            $pre.errors += "Ollama has no models pulled (or not reachable). Cloud: pull qwen. Local Grok path: use -Provider grok instead."
        } else {
            $pick = $null
            if ($Model) {
                $pick = $available | Where-Object { $_.ToLower() -eq $Model.ToLower() } | Select-Object -First 1
                if (-not $pick) {
                    $pre.warnings += "Requested model '$Model' not in Ollama; trying fallbacks. Available: $($available -join ', ')"
                }
            }
            if (-not $pick) {
                foreach ($cand in $preferredOllamaModels) {
                    $pick = $available | Where-Object { $_.ToLower() -eq $cand.ToLower() } | Select-Object -First 1
                    if ($pick) { break }
                }
            }
            if (-not $pick) {
                $pick = $available[0]
                $pre.warnings += "No preferred model found; using first available: $pick"
            }
            if ($Model -and ($Model.ToLower() -ne $pick.ToLower())) {
                $pre.warnings += "Model overridden: '$Model' -> '$pick'"
            }
            $Model = $pick
            $pre.model = $Model
            $env:PIPELINE_MODEL = $Model
        }
    } catch {
        $pre.errors += "Ollama preflight failed: $_"
    }
} elseif ($Provider -eq "grok") {
    # Local: Grok API for agents + GROK_BUILD_CMD CLI for skill steps (implement/plan/field)
    if (-not $env:XAI_API_KEY -and -not $env:GROK_API_KEY) {
        $pre.errors += "XAI_API_KEY not set (load factory .env or set in shell). Classic agents need API; CLI alone is not enough for full from-list."
    }
    if (-not $Model) {
        $Model = "grok-4.3"
        $pre.model = $Model
    }
    $env:PIPELINE_MODEL = $Model
    $pre.warnings += "Local Grok path: implement/plan/field = GROK_BUILD_CMD CLI; manager/planner agents = provider=grok API"
} else {
    if (-not $Model) {
        $Model = if ($env:PIPELINE_MODEL) { $env:PIPELINE_MODEL } else { "grok-4.3" }
        $pre.model = $Model
    }
}

# Competing jobs
$busy = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -and (
        $_.CommandLine -match "bulk_thin_field_ship" -or
        ($_.CommandLine -match "pipeline\\runner.py" -and $_.CommandLine -match "from-list")
    )
}
if ($busy) {
    $pre.warnings += "Other pipeline/bulk processes may be running (PIDs: $($busy.ProcessId -join ', '))"
}

# Disk
try {
    $drive = (Get-Item $PipelineDir).PSDrive.Name
    $freeGB = [math]::Round((Get-PSDrive $drive).Free / 1GB, 1)
    $pre.disk_free_gb = $freeGB
    if ($freeGB -lt 2) { $pre.errors += "Low disk free: ${freeGB} GiB" }
} catch {
    $pre.warnings += "disk check failed: $_"
}

$pre | ConvertTo-Json -Depth 5 | Set-Content -Path $preflightLog -Encoding utf8
Write-Host "Preflight written: $preflightLog"
$pre | ConvertTo-Json -Depth 5 | Write-Host

if ($pre.errors.Count -gt 0) {
    Write-Host "PREFLIGHT FAILED - fix errors above." -ForegroundColor Red
    exit 2
}

# P1 harness canary (HARD checks only; does not block soft n8n)
Write-Host "Running connector canary (HARD)..."
$canaryArgs = @("-u", "scripts/connector_canary.py", "--require-api", "--no-n8n")
& python @canaryArgs 2>&1 | Tee-Object -FilePath (Join-Path $logDir "connector_canary.log")
if ($LASTEXITCODE -ne 0) {
    Write-Host "CONNECTOR CANARY HARD FAIL - abort overnight." -ForegroundColor Red
    exit 2
}

if ($DryRunEnvOnly) {
    Write-Host "DryRunEnvOnly: env frozen, canary ran, not starting runner."
    exit 0
}

Write-Host ""
Write-Host "=== Starting overnight Grok from-list (serial) ===" -ForegroundColor Cyan
Write-Host "Log: $runnerLog"
Write-Host "Time limit: $TimeLimitMinutes min"
Write-Host "Keep host AWAKE. Do not start bulk field ship."
Write-Host ""

Set-Location $FactoryRoot
$ideaArgs = @()
if ($IdeasFile) { $ideaArgs += @("--ideas-file", $IdeasFile) }

$pyArgs = @(
    "-u", "pipeline/runner.py",
    "--from-list",
    "--provider", $Provider,
    "--model", $Model,
    "--parallel-seeds", "1",
    "--executors", "1",
    "--time-limit", "$TimeLimitMinutes"
)
if (-not $NoFreshListOnly) {
    $pyArgs += "--fresh-list-only"
}
$pyArgs = $pyArgs + $ideaArgs

$startIso = (Get-Date).ToUniversalTime().ToString("o")
"start $startIso" | Tee-Object -FilePath $runnerLog | Out-Null

$p = Start-Process -FilePath "python" -ArgumentList $pyArgs -WorkingDirectory $FactoryRoot `
    -NoNewWindow -PassThru -RedirectStandardOutput $runnerLog -RedirectStandardError (Join-Path $logDir "runner.err.log")
# Tee is hard with Start-Process; use Wait and then report
Wait-Process -Id $p.Id
$exit = $p.ExitCode
"end $(Get-Date -Format o) exit=$exit" | Add-Content -Path $runnerLog

Write-Host "Runner exit: $exit"

# Morning report
python -u scripts/overnight_report.py --since $startIso --log-dir $logDir 2>&1 | Tee-Object -FilePath (Join-Path $logDir "report_stdout.log")

if ($DoExtract) {
    Write-Host "Running extract.py (may take a while) ..."
    # Do not let $ErrorActionPreference=Stop kill the script on native stderr
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $extractLog = Join-Path $logDir "extract.log"
        & python -u extract.py *>&1 | Tee-Object -FilePath $extractLog
        if ($LASTEXITCODE -ne 0) {
            Write-Host "extract exit code: $LASTEXITCODE (see extract.log)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "extract failed: $_" -ForegroundColor Yellow
    } finally {
        $ErrorActionPreference = $prevEap
    }
} else {
    Write-Host "Skip extract (local default). Use -DoExtract for cloud zip under aicompete\."
}

Write-Host ""
$morningPath = Join-Path $logDir "MORNING.md"
Write-Host "Done. See $morningPath"
exit $exit
