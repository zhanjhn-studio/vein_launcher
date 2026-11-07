"""Vein Launcher 安装器（EXE 版）

两种模式共用同一套界面与安装逻辑：
    在线：从 GitHub Release 下载 VeinLauncher-win64.zip
    离线：使用 EXE 内嵌的 payload/VeinLauncher-win64.zip

安装内容：解压到 %LOCALAPPDATA%\\VeinLauncherApp → 创建桌面快捷方式 → 启动。
不需要目标机器安装 Python。
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import threading
import traceback
import urllib.request
import zipfile
from pathlib import Path

import tkinter as tk
from tkinter import messagebox, ttk

APP_NAME = "Vein Launcher"
INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "VeinLauncherApp"
RELEASE_ZIP = "VeinLauncher-win64.zip"
RELEASE_URL = (
    "https://github.com/zhanjhn-studio/vein_launcher/releases/latest/download/" + RELEASE_ZIP
)


def mode() -> str:
    if "--offline" in sys.argv or "--online" not in sys.argv and getattr(sys, "frozen", False) and "Offline" in Path(sys.executable).name:
        return "offline"
    if "--online" in sys.argv:
        return "online"
    return "offline" if payload_path().exists() else "online"


def payload_path() -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    roots = [
        base / "payload",
        base,
        Path(sys.executable).resolve().parent,
        Path(__file__).resolve().parent / "payload",
    ]
    for root in roots:
        if not root.is_dir():
            continue
        exact = root / RELEASE_ZIP
        if exact.exists():
            return exact
        for candidate in sorted(root.glob("VeinLauncher*.zip"), reverse=True):
            return candidate
    return base / "payload" / RELEASE_ZIP


def create_shortcut(target: Path, workdir: Path) -> None:
    import subprocess

    desktop = Path(os.path.expanduser("~")) / "Desktop" / f"{APP_NAME}.lnk"
    script = (
        "$s=(New-Object -COM WScript.Shell).CreateShortcut('%s');"
        "$s.TargetPath='%s';$s.WorkingDirectory='%s';"
        "$s.Description='%s';$s.Save()"
    ) % (desktop, target, workdir, APP_NAME)
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
    )


class Installer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} 安装程序")
        self.geometry("560x330")
        self.resizable(False, False)
        self.configure(bg="#12151c")

        mode_text = "离线安装（无需网络）" if mode() == "offline" else "在线安装（从 GitHub 下载）"
        tk.Label(self, text=APP_NAME, font=("Microsoft YaHei UI", 20, "bold"), fg="#e6e9f0", bg="#12151c").pack(pady=(22, 4))
        tk.Label(self, text=mode_text, font=("Microsoft YaHei UI", 10), fg="#9aa4b2", bg="#12151c").pack()
        tk.Label(
            self,
            text=f"安装位置：{INSTALL_DIR}",
            font=("Microsoft YaHei UI", 9),
            fg="#6f7a8a",
            bg="#12151c",
        ).pack(pady=(8, 12))

        self.progress = ttk.Progressbar(self, length=500, mode="determinate", maximum=100)
        self.progress.pack(pady=6)
        self.status = tk.Label(self, text="准备就绪", font=("Microsoft YaHei UI", 9), fg="#9aa4b2", bg="#12151c")
        self.status.pack(pady=4)

        self.button = tk.Button(
            self,
            text="开始安装",
            font=("Microsoft YaHei UI", 11),
            bg="#6c8cff",
            fg="white",
            activebackground="#5878e8",
            relief="flat",
            width=18,
            command=self.start,
        )
        self.button.pack(pady=14)

        if "--auto" in sys.argv:
            self.after(500, self.start)

    # ------------------------------------------------------------------
    def log(self, text: str, progress: float | None = None) -> None:
        self.status.config(text=text)
        if progress is not None:
            self.progress["value"] = progress
        self.update_idletasks()

    def start(self) -> None:
        self.button.config(state="disabled")
        threading.Thread(target=self.install, daemon=True).start()

    def install(self) -> None:
        try:
            if mode() == "offline":
                source = payload_path()
                if not source.exists():
                    self.fail(f"安装包内缺少 {RELEASE_ZIP}，请改用在线安装器。")
                    return
                self.log(f"使用内置安装包（{source.stat().st_size / 1024 / 1024:.0f} MB）", 10)
                zip_path = source
            else:
                self.log("正在下载安装包…", 5)
                zip_path = Path(tempfile.gettempdir()) / RELEASE_ZIP
                self.download(RELEASE_URL, zip_path)

            self.log("正在解压…", 45)
            # 每次安装用独立 staging（并发安装时不会互抢文件）
            for old in INSTALL_DIR.parent.glob(INSTALL_DIR.name + ".staging*"):
                shutil.rmtree(old, ignore_errors=True)
            staging = INSTALL_DIR.with_name(f"{INSTALL_DIR.name}.staging-{os.getpid()}")
            shutil.rmtree(staging, ignore_errors=True)
            staging.mkdir(parents=True, exist_ok=True)
            self.extract_with_retry(zip_path, staging)

            self.log("正在替换旧版本…", 70)
            if INSTALL_DIR.exists():
                shutil.rmtree(INSTALL_DIR, ignore_errors=True)
            if INSTALL_DIR.exists():
                # 还有文件被占用：通常是有启动器在运行
                raise RuntimeError(
                    f"安装目录被占用：{INSTALL_DIR}\n请先关闭正在运行的 Vein Launcher 再重试。"
                )
            staging.rename(INSTALL_DIR)

            exe = INSTALL_DIR / "VeinLauncher.exe"
            if not exe.exists():
                candidates = list(INSTALL_DIR.rglob("VeinLauncher.exe"))
                if not candidates:
                    self.fail("解压后没有找到 VeinLauncher.exe")
                    return
                exe = candidates[0]

            self.log("正在创建桌面快捷方式…", 80)
            create_shortcut(exe, exe.parent)

            self.log("安装完成，正在启动…", 100)
            os.startfile(str(exe))
            if "--auto" in sys.argv:
                self.after(1500, self.destroy)
                return
            messagebox.showinfo(APP_NAME, f"安装完成！\n\n位置：{exe.parent}\n\n桌面快捷方式已创建。")
        except Exception as exc:  # 安装失败的兜底提示
            self.fail(str(exc))

    def extract_with_retry(self, zip_path: Path, target_dir: Path, attempts: int = 8) -> None:
        """逐文件解压；遇到杀毒软件短暂锁文件就退避重试"""
        import time

        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            for index, name in enumerate(names, 1):
                if name.endswith("/"):
                    continue
                destination = target_dir / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                for attempt in range(attempts):
                    try:
                        with archive.open(name) as source, open(destination, "wb") as handle:
                            shutil.copyfileobj(source, handle)
                        break
                    except PermissionError:
                        if attempt == attempts - 1:
                            raise
                        time.sleep(0.4 + attempt * 0.3)
                if index % 200 == 0:
                    self.log(f"解压中 {index}/{len(names)}…", 45 + index / len(names) * 20)

    def download(self, url: str, target: Path) -> None:
        request = urllib.request.Request(url, headers={"User-Agent": "VeinLauncherInstaller"})
        with urllib.request.urlopen(request, timeout=60) as response:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            with target.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    handle.write(chunk)
                    done += len(chunk)
                    if total:
                        percent = min(44, 5 + done / total * 38)
                        self.log(f"下载中 {done / 1024 / 1024:.0f} / {total / 1024 / 1024:.0f} MB", percent)
        self.log("下载完成", 45)

    def fail(self, message: str) -> None:
        try:
            detail = traceback.format_exc()
            Path(os.environ.get("TEMP", ".")).joinpath("vl_install_error.txt").write_text(
                message + "\n\n" + detail, encoding="utf-8"
            )
        except Exception:
            pass
        self.log("安装失败：" + message, 0)
        messagebox.showerror(APP_NAME, message)
        self.button.config(state="normal")


def inspect_payload() -> None:
    import zipfile

    info = []
    info.append(f"frozen={getattr(sys, 'frozen', False)}")
    info.append(f"meipass={getattr(sys, '_MEIPASS', '')}")
    source = payload_path()
    info.append(f"payload={source}")
    info.append(f"exists={source.exists()}")
    if source.exists():
        info.append(f"size={source.stat().st_size}")
        try:
            with zipfile.ZipFile(source) as archive:
                names = archive.namelist()
                bad = archive.testzip()
                info.append(f"entries={len(names)} bad={bad}")
                info.append(f"head={names[:3]}")
        except Exception as exc:
            info.append(f"zip_error={exc}")
    Path(os.environ.get("TEMP", ".")) .joinpath("vl_payload_info.txt").write_text(
        "\n".join(info), encoding="utf-8"
    )


if __name__ == "__main__":
    if "--inspect" in sys.argv:
        inspect_payload()
        sys.exit(0)
    Installer().mainloop()
