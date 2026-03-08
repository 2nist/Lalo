param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('machine-a', 'machine-b', 'machine-c')]
    [string]$MachineId,

    [int]$IntervalSec = 20,
    [switch]$Once,
    [string]$RepoRoot = '',
    [string]$NetworkMirrorPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = (Resolve-Path (Join-Path $scriptDir '..\\..')).Path
}

function Get-ChannelPath {
    param(
        [string]$Base,
        [string]$Id
    )
    return Join-Path $Base ("docs\planning\machines\comms\live\{0}.md" -f $Id)
}

function Try-SyncFromNetworkMirror {
    param(
        [string]$NetworkPath,
        [string]$LocalPath
    )

    if ([string]::IsNullOrWhiteSpace($NetworkPath)) {
        return
    }

    if (-not (Test-Path $NetworkPath)) {
        Write-Host "[warn] Network mirror not found: $NetworkPath" -ForegroundColor Yellow
        return
    }

    try {
        Copy-Item -Path $NetworkPath -Destination $LocalPath -Force
    }
    catch {
        Write-Host "[warn] Mirror sync failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Get-OpenMessages {
    param([string]$Content)

    $blocks = [regex]::Split($Content, "(?m)^## ") | Where-Object { $_.Trim() -ne '' }
    $open = @()

    foreach ($b in $blocks) {
        if ($b -match '(?im)^status:\s*open\s*$') {
            $msgId = ($b -split "`r?`n")[0].Trim()
            $open += $msgId
        }
    }

    return @($open)
}

$channelPath = Get-ChannelPath -Base $RepoRoot -Id $MachineId
if (-not (Test-Path $channelPath)) {
    throw "Channel file not found: $channelPath"
}

$lastHash = ''
Write-Host "Watching channel: $channelPath" -ForegroundColor Cyan
if ($NetworkMirrorPath) {
    Write-Host "Network mirror: $NetworkMirrorPath" -ForegroundColor Cyan
}

while ($true) {
    Try-SyncFromNetworkMirror -NetworkPath $NetworkMirrorPath -LocalPath $channelPath

    $content = Get-Content -Path $channelPath -Raw -ErrorAction Stop
    $hash = [System.BitConverter]::ToString((New-Object Security.Cryptography.SHA256Managed).ComputeHash([Text.Encoding]::UTF8.GetBytes($content)))

    if ($hash -ne $lastHash) {
        $lastHash = $hash
        $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $openMessages = @(Get-OpenMessages -Content $content)

        Write-Host "[$now] change detected" -ForegroundColor Green
        if ($openMessages.Count -gt 0) {
            Write-Host "Open messages:" -ForegroundColor Yellow
            $openMessages | ForEach-Object { Write-Host "- $_" -ForegroundColor Yellow }
        }
        else {
            Write-Host "No open messages." -ForegroundColor DarkGray
        }

        Write-Host "--- tail ---" -ForegroundColor DarkCyan
        Get-Content -Path $channelPath -Tail 40
        Write-Host "-----------" -ForegroundColor DarkCyan
    }

    if ($Once) {
        break
    }

    Start-Sleep -Seconds $IntervalSec
}
