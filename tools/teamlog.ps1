# Append one entry to teamwork.md
# Usage: powershell -File tools\teamlog.ps1 -Area "ui/sidebar" -What "280ms expand" -Files "src/styles.css" -Verification "tests 44 OK" -Commit "38942ad"
param(
  [Parameter(Mandatory = $true)][string]$Area,
  [Parameter(Mandatory = $true)][string]$What,
  [string]$Files = "",
  [string]$Verification = "",
  [string]$Commit = "",
  [string]$LogPath = "teamwork.md"
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$log = Join-Path $root $LogPath
if (-not (Test-Path $log)) { throw "teamwork.md not found at $log" }

$date = Get-Date -Format "yyyy-MM-dd"
$parts = @("**$date · $Area** — $What")
if ($Files) { $parts += "` · $Files" }
if ($Verification) { $parts += "` · $Verification" }
if ($Commit) { $parts += "` · ``$Commit``" }
$line = "- " + ($parts -join "")

Add-Content -Path $log -Value $line -Encoding UTF8
Write-Host "appended: $line"
