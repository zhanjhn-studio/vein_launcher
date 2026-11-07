"""离线预览前端界面：mock 掉 QWebChannel，把真实 UI 渲染成 PNG

用法：python tools/ui_preview.py [页面] [输出.png]
     python tools/ui_preview.py launch  preview_launch.png
     python tools/ui_preview.py download preview_download.png

依赖：PySide6（项目已有）。生成的是 dist/ 里真实前端，样式改动可立即看到。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "vein_launcher" / "presentation" / "webui" / "dist"

MOCK = r"""
<script>
(function () {
  const ACCOUNTS = [
    { id: 'a1', username: 'Steve', selected: true, type: 'offline', online: false },
    { id: 'a2', username: 'Alex', selected: false, type: 'littleskin', online: true }
  ];
  const VERSIONS = [
    { id: '1.20.1', type: 'release' },
    { id: '1.20.1-forge', type: 'release' },
    { id: '1.21.1', type: 'release' }
  ];
  const ANNOUNCEMENTS = {
    version: '0.1.0', current: '0.1.0', force_update: false, min_version: '',
    announcements: [
      { id: 'n1', level: 'light', title: 'Vein Launcher 0.1.0 is out',
        content: 'One-click updates, LittleSkin library and a brand-new instance manager.' },
      { id: 'n2', level: 'light', title: 'LittleSkin library is live',
        content: 'Browse public skins and download them straight into an account.' }
    ],
    update: {}
  };
  const SKINS = [
    { id: 'a1', username: 'Steve', type: 'offline', skin: { has: true } },
    { id: 'a2', username: 'Alex', type: 'littleskin', online: true, skin: { has: false } }
  ];
  const LIBRARY = {
    page: 1, has_more: true,
    items: [
      { tid: 1, name: 'knight', type: 'classic', hd: false, likes: 12, author: 'zhan', preview: '' },
      { tid: 2, name: 'slim girl', type: 'slim', hd: true, likes: 88, author: 'alex', preview: '' },
      { tid: 3, name: 'hoodie', type: 'classic', hd: false, likes: 5, author: 'steve', preview: '' },
      { tid: 4, name: 'cyan', type: 'slim', hd: false, likes: 31, author: 'jeb', preview: '' }
    ]
  };

  function answer(method, args) {
    switch (method) {
      case 'app.info':
        return { version: '0.1.0', dataDir: 'C:/VeinLauncher', firstRun: false, accountCount: 2 };
      case 'versions.info': return VERSIONS;
      case 'accounts.list': return ACCOUNTS;
      case 'announcements.get': return ANNOUNCEMENTS;
      case 'update.latest': return { available: false, current: '0.1.0' };
      case 'ui.prefs': return { compactMode: false, idleSeconds: 60, wallpaper: null };
      case 'i18n.get': return { lang: 'en_US' };
      case 'downloads.list': return [];
      case 'mlc.state': return { connected: false, pid: null };
      case 'game.running': return { games: [
        { pid: 8420, version_id: '1.20.1', source: 'launcher', started_at: 0, uptime: 1290, memory_mb: 1487, title: 'Minecraft', game_dir: '' },
        { pid: 9312, version_id: '1.20.1-forge', source: 'external', started_at: 0, uptime: 95, memory_mb: 892, title: 'Minecraft', game_dir: '' },
      ], count: 2 };
      case 'java.detect': return [{ path: 'C:/Java/bin/java.exe', major: 17, version: '17.0.8', vendor: 'Temurin' }];
      case 'minecraft.getDir': return { path: 'C:/VeinLauncher/minecraft' };
      case 'accounts.msClientId': return { client_id: '' };
      case 'accounts.msAuthority': return { authority: 'common' };
      case 'skins.list': return SKINS;
      case 'skins.library': return LIBRARY;
      case 'instances.contents': return {
        mod: [{ name: 'sodium.jar', enabled: true, size: 2200000, dir: false },
              { name: 'iris.jar', enabled: true, size: 8400000, dir: false },
              { name: 'old-mod.jar', enabled: false, size: 512000, dir: false }],
        resourcepack: [{ name: 'Faithful.zip', enabled: true, size: 12000000, dir: false }],
        shader: [{ name: 'BSL.zip', enabled: true, size: 3000000, dir: false }],
        datapack: [], modpack: []
      };
      case 'instances.worlds': return [
        { name: 'Survival', seed: -2281200821074172928, version: '1.20.1', folder: 'Survival', instance: '1.20.1' },
        { name: 'Creative', seed: 123456789, version: '1.20.1', folder: 'Creative', instance: '1.20.1' }
      ];
      case 'versions.remote': return [
        { id: '1.21.1', type: 'release', release_time: '2025-01-01' },
        { id: '1.20.1', type: 'release', release_time: '2023-06-12' }
      ];
      case 'mods.featured': return [
        { slug: 'sodium', title: 'Sodium', description: 'Modern rendering engine', icon: 'icons/crafting_table.png',
          downloads: 1234567, author: 'jellysquid', type: 'mod', url: '' },
        { slug: 'iris', title: 'Iris Shaders', description: 'Shaders for Fabric', icon: 'icons/spyglass.png',
          downloads: 987654, author: 'coderbot', type: 'mod', url: '' }
      ];
      default: return null;
    }
  }

  class MockBridge {
    call(id, raw) {
      let req = {};
      try { req = JSON.parse(raw); } catch (e) { req = {}; }
      const payload = answer(req.method, (req.params || {}).args || []);
      setTimeout(() => {
        if (window.__veinResult) window.__veinResult(id, true, payload);
      }, 0);
    }
  }

  window.QWebChannel = function (transport, cb) {
    cb({ objects: { bridge: new MockBridge() } });
  };
  window.qt = window.qt || { webChannelTransport: {} };
})();
</script>
"""


def build_preview(page: str, expand: bool = False) -> Path:
    index = DIST / "index.html"
    html = index.read_text(encoding="utf-8")
    marker = '<script src="app.js"></script>'
    extra = ""
    if expand:
        extra = (
            "<style>.side{width:208px!important}"
            ".side-brand span,.side-btn .txt,.theme-btn .txt,.side-ver{opacity:1!important;"
            "transform:none!important}</style>"
        )
    html = html.replace(marker, MOCK + "\n" + extra + "\n" + marker)
    html = html.replace(
        '<script src="app.js"></script>',
        f'<script>window.location.hash = "#/{page}";</script>\n<script src="app.js"></script>',
    )
    out = DIST / f"preview_{page}.html"
    out.write_text(html, encoding="utf-8")
    return out


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    expand = "--expand" in sys.argv
    page = args[0] if args else "launch"
    out = Path(args[1]) if len(args) > 1 else ROOT / "docs" / f"preview_{page}.png"

    html = build_preview(page, expand)
    app = QApplication(sys.argv[:1])
    view = QWebEngineView()
    view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    view.resize(1280, 820)
    view.show()
    view.page().setBackgroundColor(QColor("#0f1218"))

    def grab() -> None:
        image = view.grab()
        out.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(out))
        print(f"saved: {out} ({image.width()}x{image.height()})")
        app.quit()

    view.loadFinished.connect(lambda ok: QTimer.singleShot(3200, grab))
    view.load(QUrl.fromLocalFile(str(html)))
    QTimer.singleShot(20000, app.quit)
    app.exec()
    return 0


if __name__ == "__main__":
    sys.exit(main())
