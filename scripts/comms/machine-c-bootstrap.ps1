param(
    [switch]$Run,
    [switch]$FetchHarmonixIfMissing,
    [switch]$FetchAudioIfMissing,
    [int]$AudioMax = 30,
    [string]$RepoRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = (Resolve-Path (Join-Path $scriptDir '..\..')).Path
}

$harmonixDir = Join-Path $RepoRoot 'data\raw\harmonix'
$audioDir = Join-Path $RepoRoot 'data\audio'
$validateScript = Join-Path $RepoRoot 'tmp\validate_pipeline.py'
$sampleAudio = Join-Path $RepoRoot 'third_party\BTC-ISMIR19\test\example.mp3'

$resultsDir = Join-Path $RepoRoot 'results'
$validateLog = Join-Path $resultsDir 'validate-machine-c.log'
$benchLog = Join-Path $resultsDir 'bench-machine-c.log'
$benchOut = Join-Path $resultsDir 'sections-machine-c.json'

Write-Host "[machine-c-bootstrap] RepoRoot: $RepoRoot" -ForegroundColor Cyan
Write-Host "[check] harmonix dir: $(Test-Path $harmonixDir) -> $harmonixDir"
Write-Host "[check] audio dir: $(Test-Path $audioDir) -> $audioDir"
Write-Host "[check] validate script: $(Test-Path $validateScript) -> $validateScript"
Write-Host "[check] sample audio: $(Test-Path $sampleAudio) -> $sampleAudio"

if (-not (Test-Path $resultsDir)) {
    New-Item -ItemType Directory -Force -Path $resultsDir | Out-Null
}

$hasHarmonixAudio = $false
if (Test-Path $audioDir) {
    $audioCount = (
        Get-ChildItem -Path $audioDir -Filter 'harmonix_*' -File -ErrorAction SilentlyContinue |
        Measure-Object
    ).Count
    $hasHarmonixAudio = $audioCount -gt 0
    Write-Host "[check] harmonix audio files: $audioCount"
}

if (-not (Test-Path $harmonixDir) -and $FetchHarmonixIfMissing) {
    Write-Host "[action] Harmonix missing; running fetch script..." -ForegroundColor Yellow
    Push-Location $RepoRoot
    try {
        python scripts/datasets/fetch_harmonix.py
    }
    finally {
        Pop-Location
    }
}

if ((-not $hasHarmonixAudio) -and $FetchAudioIfMissing) {
    Write-Host "[action] Harmonix audio missing; running audio fetch script..." -ForegroundColor Yellow
    Push-Location $RepoRoot
    try {
        python scripts/datasets/fetch_harmonix_audio.py --max $AudioMax --resume
    }
    finally {
        Pop-Location
    }
}

$commands = @()

if (Test-Path $validateScript) {
    $commands += 'python tmp/validate_pipeline.py *> results/validate-machine-c.log'
}
else {
    Write-Host '[info] tmp/validate_pipeline.py missing; validation step will be skipped.' -ForegroundColor Yellow
}

$commands += 'python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/sections-machine-c.json *> results/bench-machine-c.log'

Write-Host ''
Write-Host 'Recommended commands:' -ForegroundColor Green
$commands | ForEach-Object { Write-Host "  $_" }

if (-not (Test-Path $harmonixDir)) {
    Write-Host '[warn] Harmonix annotations missing. Run with -FetchHarmonixIfMissing.' -ForegroundColor Yellow
}

if (-not $hasHarmonixAudio) {
    Write-Host '[warn] Harmonix audio missing. Run with -FetchAudioIfMissing (yt-dlp required).' -ForegroundColor Yellow
}

if (-not $Run) {
    Write-Host ''
    Write-Host 'Use -Run to execute commands automatically.' -ForegroundColor DarkGray
    exit 0
}

Push-Location $RepoRoot
try {
    foreach ($cmd in $commands) {
        Write-Host "[run] $cmd" -ForegroundColor Cyan
        Invoke-Expression $cmd
    }
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host 'Artifacts:' -ForegroundColor Green
if (Test-Path $validateLog) { Write-Host "  $validateLog" }
if (Test-Path $benchOut) { Write-Host "  $benchOut" }
if (Test-Path $benchLog) { Write-Host "  $benchLog" }
