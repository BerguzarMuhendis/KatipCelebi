# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/faruk/Desktop/KatipCelebi/src/app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/faruk/Desktop/KatipCelebi/assets', 'assets'), ('C:/Users/faruk/Desktop/KatipCelebi/src', 'src')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:/Users/faruk/Desktop/KatipCelebi/assets/katipcelebi.ico'],
)
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
