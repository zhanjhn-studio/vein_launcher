# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['pydantic']
hiddenimports += collect_submodules('vein_launcher')


a = Analysis(
    ['Z:\\Vein Launche\\run_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('Z:\\Vein Launche\\vein_launcher\\presentation\\ui\\theme', 'vein_launcher/presentation/ui/theme'), ('Z:\\Vein Launche\\vein_launcher\\common\\i18n\\locales', 'vein_launcher/common/i18n/locales'), ('Z:\\Vein Launche\\vein_launcher\\infrastructure\\plugin_host\\runtime', 'vein_launcher/infrastructure/plugin_host/runtime'), ('Z:\\Vein Launche\\plugins_examples', 'plugins_examples')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VeinLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VeinLauncher',
)
