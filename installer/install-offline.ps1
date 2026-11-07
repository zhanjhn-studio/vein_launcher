# Vein Launcher 离线安装器
# 不联网：使用 installer\payload 下的 zip（和可选的 wheels）完成安装。
param(
    [string]$InstallDir = "$env:LOCALAPPDATA\VeinLauncherApp",
    [string]$Payload = "",
    [switch]$NoShortcut,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

function Write-Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }
function Write-Ok($text) { Write-Host "    $text" -ForegroundColor Green }
function Write-Fail($text) { Write-Host "    $text" -ForegroundColor Red }

function Find-Python {
    foreach ($candidate in @("python", "py")) {
        try {
            $version = & $candidate -c "import sys;print('%d.%d'%sys.version_info[:2])" 2>$null
            if ($LASTEXITCODE -eq 0 -and $version) {
                $parts = $version.Split(".")
                if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 10) { return $candidate }
            }
        } catch {}
    }
    return $null
}

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $Payload) {
    $Payload = Get-ChildItem (Join-Path $here "payload") -Filter "VeinLauncher-*.zip" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
}
$wheels = Join-Path $here "payload\wheels"

Write-Host ""
Write-Host "  Vein Launcher - Offline installer" -ForegroundColor White
Write-Host ""

if (-not $Payload -or -not (Test-Path $Payload)) {
    Write-Fail "找不到离线安装包：installer\payload\VeinLauncher-*.zip"
    Write-Host "    生成方法：在有网的电脑上运行 installer\build-payload.ps1，" -ForegroundColor Yellow
    Write-Host "    再把整个 installer 目录（含 payload）拷贝到目标机器。" -ForegroundColor Yellow
    Read-Host "按回车退出"
    exit 1
}
Write-Ok ("使用安装包 " + (Split-Path -Leaf $Payload))

Write-Step "检查 Python 3.10+"
$python = Find-Python
if (-not $python) {
    Write-Fail "没有找到 Python 3.10+。离线环境请提前安装 Python，或使用带嵌入式运行时的安装包。"
    Read-Host "按回车退出"
    exit 1
}
Write-Ok "使用 $python"

Write-Step "解压到 $InstallDir"
if (Test-Path $InstallDir) {
    Write-Ok "目标目录已存在，覆盖更新"
    Remove-Item $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
Expand-Archive -LiteralPath $Payload -DestinationPath $InstallDir -Force
Write-Ok "解压完成"

Write-Step "创建虚拟环境"
$venv = Join-Path $InstallDir ".venv"
if (-not (Test-Path $venv)) {
    & $python -m venv $venv
}
$pip = Join-Path $venv "Scripts\pip.exe"

Write-Step "安装依赖（离线优先使用本地 wheels）"
if (Test-Path $wheels) {
    & $pip install --no-index --find-links $wheels -r (Join-Path $InstallDir "requirements.txt") --quiet
} else {
    $payloadInner = Join-Path $InstallDir "VeinLauncher"
    if (Test-Path (Join-Path $payloadInner "wheels")) {
        & $pip install --no-index --find-links (Join-Path $payloadInner "wheels") -r (Join-Path $InstallDir "requirements.txt") --quiet
    } else {
        Write-Ok "没有本地 wheels，尝试从已安装环境复制依赖"
        & $python -c "import PySide6, aiohttp, pydantic" 2>$null
        if ($LASTEXITCODE -eq 0) {
            & $pip install PySide6 aiohttp pydantic requests psutil --quiet
        } else {
            Write-Fail "本机没有可用依赖，也没有 wheels 缓存。"
            Write-Fail "请在有网机器上执行：pip download -r requirements.txt -d payload\wheels"
            Read-Host "按回车退出"
            exit 1
        }
    }
}
Write-Ok "依赖就绪"

if (-not $NoShortcut) {
    Write-Step "创建桌面快捷方式"
    $pythonw = Join-Path $venv "Scripts\pythonw.exe"
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Desktop")) "Vein Launcher.lnk"))
    $link.TargetPath = $pythonw
    $link.Arguments = "-m vein_launcher.presentation.main"
    $link.WorkingDirectory = $InstallDir
    $link.Description = "Vein Launcher"
    $link.Save()
    Write-Ok "桌面快捷方式已创建"
}

if (-not $NoLaunch) {
    Write-Step "启动 Vein Launcher"
    $moduleDir = Get-ChildItem $InstallDir -Directory |
        Where-Object { Test-Path (Join-Path $_.FullName "vein_launcher") } |
        Select-Object -First 1
    $work = if ($moduleDir) { $moduleDir.FullName } else { $InstallDir }
    Start-Process -FilePath (Join-Path $venv "Scripts\pythonw.exe") -ArgumentList "-m", "vein_launcher.presentation.main" -WorkingDirectory $work
    Write-Ok "已启动"
}

Write-Host ""
Write-Host "  安装完成：$InstallDir" -ForegroundColor Green
Write-Host ""
Read-Host "按回车关闭"
