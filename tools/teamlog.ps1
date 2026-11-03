# Append one entry to teamwork.md
# Usage: powershell -File tools\teamlog.ps1 -Area "ui/sidebar" -What "280ms expand" `
#          -Files "styles.css" -Verification "tests 44 OK" -Commit "38942ad"
# Keep arguments ASCII: the Windows console can mangle non-ASCII arguments.
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
$parts = @("**$date | $Area** - $What")
if ($Files) { $parts += " | files: $Files" }
if ($Verification) { $parts += " | verify: $Verification" }
if ($Commit) { $parts += " | commit: $Commit" }
$line = "- " + ($parts -join "")

$utf8 = New-Object System.Text.UTF8Encoding($false)
$existing = [System.IO.File]::ReadAllText($log, [System.Text.Encoding]::UTF8)
if (-not $existing.EndsWith("`n")) { $existing += "`n" }
[System.IO.File]::WriteAllText($log, $existing + $line + "`n", $utf8)
Write-Host "appended: $line"
