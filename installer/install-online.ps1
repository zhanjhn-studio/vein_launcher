# Vein Launcher 在线安装器
# 从 GitHub 拉取源码并安装；失败时提示改用离线安装器。
param(
    [string]$InstallDir = "$env:LOCALAPPDATA\VeinLauncherApp",
    [string]$Branch = "main",
    [string]$Repo = "zhanjhn-studio/vein_launcher",
    [switch]$NoShortcut,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

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

Write-Host ""
Write-Host "  Vein Launcher - Online installer" -ForegroundColor White
Write-Host ""

Write-Step "检查 Python 3.10+"
$python = Find-Python
if (-not $python) {
    Write-Fail "没有找到 Python 3.10+，请先安装：https://www.python.org/downloads/"
    Write-Fail "安装时记得勾选 Add python.exe to PATH"
    Read-Host "按回车退出"
    exit 1
}
Write-Ok "使用 $python ($(& $python -c 'import sys;print(sys.version.split()[0])'))"

Write-Step "下载源码（$Repo @ $Branch）"
$zip = Join-Path $env:TEMP "vein_launcher_$([guid]::NewGuid().ToString('N')).zip"
$url = "https://codeload.github.com/$Repo/zip/refs/heads/$Branch"
try {
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing -TimeoutSec 120
    Write-Ok ("下载完成 " + [math]::Round((Get-Item $zip).Length / 1MB, 1) + " MB")
} catch {
    Write-Fail "下载失败：$($_.Exception.Message)"
    Write-Host ""
    Write-Host "  请改用离线安装器：先在有网的电脑上运行 build-payload.ps1，" -ForegroundColor Yellow
    Write-Host "  把生成的 installer\\payload 目录整个拷过来，再双击 install-offline.cmd" -ForegroundColor Yellow
    Read-Host "按回车退出"
    exit 1
}

Write-Step "解压到 $InstallDir"
$temp = Join-Path $env:TEMP "vein_extract_$([guid]::NewGuid().ToString('N'))"
Expand-Archive -LiteralPath $zip -DestinationPath $temp -Force
$root = Get-ChildItem $temp -Directory | Select-Object -First 1
if (-not $root) { Write-Fail "压缩包结构异常"; exit 1 }
if (Test-Path $InstallDir) {
    Write-Ok "目标目录已存在，覆盖更新"
    Remove-Item $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
Copy-Item (Join-Path $root.FullName "*") $InstallDir -Recurse -Force
Remove-Item $temp, $zip -Recurse -Force -ErrorAction SilentlyContinue
Write-Ok "代码已就位"

Write-Step "创建虚拟环境并安装依赖"
$venv = Join-Path $InstallDir ".venv"
if (-not (Test-Path $venv)) {
    & $python -m venv $venv
}
$pip = Join-Path $venv "Scripts\pip.exe"
& $pip install --upgrade pip --quiet
& $pip install -r (Join-Path $InstallDir "requirements.txt") --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Fail "依赖安装失败，请检查网络后重试"
    Read-Host "按回车退出"
    exit 1
}
Write-Ok "依赖安装完成"

if (-not $NoShortcut) {
    Write-Step "创建桌面快捷方式"
    $pythonw = Join-Path $venv "Scripts\pythonw.exe"
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Desktop")) "Vein Launcher.lnk"))
    $link.TargetPath = $pythonw
    $link.Arguments = "-m vein_launcher.presentation.main"
    $link.WorkingDirectory = $InstallDir
    $link.IconLocation = (Join-Path $InstallDir "assets\icons\chest.ico")
    $link.Description = "Vein Launcher"
    $link.Save()
    Write-Ok "桌面快捷方式已创建"
}

if (-not $NoLaunch) {
    Write-Step "启动 Vein Launcher"
    Start-Process -FilePath (Join-Path $venv "Scripts\pythonw.exe") -ArgumentList "-m", "vein_launcher.presentation.main" -WorkingDirectory $InstallDir
    Write-Ok "已启动"
}

Write-Host ""
Write-Host "  安装完成：$InstallDir" -ForegroundColor Green
Write-Host "  数据目录：$InstallDir\VeinLauncher（配置、日志、游戏文件都在这里）" -ForegroundColor Gray
Write-Host ""
Read-Host "按回车关闭"
