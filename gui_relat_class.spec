# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui_relat_class.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Alan Amorim\\Desktop\\SCRIPT PYTHON PARA EXTRAÇÃO DE DADOS DA COLUNA RCL_TXT\\RELATÓRIO DA CLASSIFICAÇÃO\\icone_relat_class.ico', '.')],
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
    name='gui_relat_class',
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
    icon=['C:\\Users\\Alan Amorim\\Desktop\\SCRIPT PYTHON PARA EXTRAÇÃO DE DADOS DA COLUNA RCL_TXT\\RELATÓRIO DA CLASSIFICAÇÃO\\icone_relat_class.ico'],
)
