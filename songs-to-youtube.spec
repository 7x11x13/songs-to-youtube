# -*- mode: python ; coding: utf-8 -*-

import PySide6
import shiboken6
import os
import sys

PYSIDE_PATH = PySide6.__path__[0]
SHIBOKEN_PATH = shiboken6.__path__[0]

if sys.platform == 'darwin':
    binaries = [(os.path.join(PYSIDE_PATH, 'Qt', 'plugins', 'platforms', '*'), 'platforms'),
              (os.path.join(PYSIDE_PATH, 'Qt', 'plugins', 'styles', '*'), 'styles')]
elif sys.platform == 'win32' or sys.platform == 'cygwin':
    binaries = [(os.path.join(PYSIDE_PATH, 'plugins', 'platforms', '*'), 'platforms'),
     (os.path.join(PYSIDE_PATH, 'plugins', 'styles', '*'), 'styles')]
else:
    binaries = [(os.path.join(PYSIDE_PATH, 'Qt', 'plugins', 'platforms', '*'), 'platforms'),
              (os.path.join(PYSIDE_PATH, 'Qt', 'plugins', 'platformthemes', '*'), 'platformthemes')]

block_cipher = None


a = Analysis(['main.py'],
             pathex=[SHIBOKEN_PATH, '.'],
             binaries=binaries,
             hiddenimports=['PySide6.QtXml'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='songs-to-youtube',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='songs-to-youtube')
