# -*- mode: python -*-

import os
import glob
import platform


block_cipher = None
os_name = platform.system()
binaries = []

data_files = []


a = Analysis(['beem/cli.py'],
             pathex=['beem'],
             binaries=binaries,
             datas=data_files,
             hiddenimports=['scrypt'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['matplotlib', 'scipy', 'pandas', 'numpy', 'PyQt5', 'tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='beempy',
    debug=False,
    strip=False,
    upx=False,
    console=True,
    icon='beempy.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='beempy',
    strip=False,
    upx=False
)