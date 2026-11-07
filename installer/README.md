# Vein Launcher 安装器（在线 / 离线）

两套安装方式，装出来**完全一样**，区别只有「代码从哪来」：

| 方式 | 脚本 | 需要网络 | 适用场景 |
|---|---|---|---|
| 在线安装 | `install-online.cmd` | 是（拉 GitHub 源码） | 能访问 GitHub 的正常情况 |
| 离线安装 | `install-offline.cmd` | 否（用本地 payload） | GitHub 打不开 / 加速器 / U 盘分发 |

## 在线安装

双击 `install-online.cmd`，或在 PowerShell 里：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-online.ps1
```

它会：下载 `zhanjhn-studio/vein_launcher` 的 main 分支 → 解压到 `%LOCALAPPDATA%\VeinLauncherApp` →
创建 `.venv` 并安装依赖 → 生成桌面快捷方式 → 启动。

可选参数：

```powershell
.\install-online.ps1 -InstallDir "D:\Games\VeinLauncher" -Branch main -NoShortcut -NoLaunch
```

## 离线安装

1. 把 `payload/VeinLauncher-<版本>.zip` 放在本目录的 `payload/` 下
   （由 `build-payload.ps1` 生成，或从 Release 下载）
2. 双击 `install-offline.cmd`

它不会联网，只解压 payload、创建 `.venv`、装**随包附带的 wheel 缓存**（如果存在 `payload/wheels/`），
否则尝试从本机已有的 Python 环境安装依赖；再生成快捷方式。

## 生成离线 payload

```powershell
powershell -ExecutionPolicy Bypass -File .\build-payload.ps1
```

会调用 `tools/package_release.py --jre` 生成 zip，并复制到 `payload/`。
