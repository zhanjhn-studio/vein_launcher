# 生成离线安装器所需的 payload（zip + wheels）
param(
    [switch]$WithoutWheels
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here
$payload = Join-Path $here "payload"
New-Item -ItemType Directory -Path $payload -Force | Out-Null

Write-Host "==> 打包发布 zip（含最小 JRE）" -ForegroundColor Cyan
Push-Location $root
try {
    python tools\package_release.py --jre
} finally {
    Pop-Location
}

$zip = Get-ChildItem (Join-Path $root "dist_release") -Filter "VeinLauncher-*.zip" |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $zip) { throw "没有生成 zip，检查 tools/package_release.py 输出" }
Copy-Item $zip.FullName $payload -Force
Write-Host "    payload: $($zip.Name) ($([math]::Round($zip.Length/1MB,1)) MB)" -ForegroundColor Green

if (-not $WithoutWheels) {
    Write-Host "==> 下载依赖 wheels（离线安装必需）" -ForegroundColor Cyan
    $wheels = Join-Path $payload "wheels"
    New-Item -ItemType Directory -Path $wheels -Force | Out-Null
    python -m pip download -r (Join-Path $root "requirements.txt") -d $wheels
    $size = (Get-ChildItem $wheels -Recurse -File | Measure-Object Length -Sum).Sum
    Write-Host ("    wheels: " + [math]::Round($size / 1MB, 1) + " MB -> " + $wheels) -ForegroundColor Green
}

Write-Host ""
Write-Host "离线安装包就绪：$payload" -ForegroundColor Green
