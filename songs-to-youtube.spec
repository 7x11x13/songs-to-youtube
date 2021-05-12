# -*- mode: python ; coding: utf-8 -*-

import PySide6
import shiboken6
import os
import sys

PYSIDE_PATH = PySide6.__path__[0]
SHIBOKEN_PATH = shiboken6.__path__[0]

if sys.platform == 'darwin':
    pyside_includes = ('platforms', 'styles', 'iconengines', 'imageformats')
    binaries = [(os.path.join(PYSIDE_PATH, 'Qt', 'plugins', name, '*'), name) for name in pyside_includes]
elif sys.platform == 'win32' or sys.platform == 'cygwin':
    pyside_includes = ('platforms', 'styles', 'iconengines', 'imageformats')
    binaries = [(os.path.join(PYSIDE_PATH, 'plugins', name, '*'), name) for name in pyside_includes]
else:
    pyside_includes = ('platforms', 'platformthemes', 'iconengines', 'imageformats', 'platforminputcontexts')
    binaries = [(os.path.join(PYSIDE_PATH, 'Qt', 'plugins', name, '*'), name) for name in pyside_includes]

block_cipher = None


a = Analysis(['main.py'],
             pathex=[SHIBOKEN_PATH, '.'],
             binaries=binaries,
             datas=[('ui/*.ui', 'ui'),
                    ('config/*.ini', 'config'),
                    ('commands/concat/*.command', 'commands/concat'),
                    ('commands/render/*.command', 'commands/render')],
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
          console=False,
          icon='image/icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='songs-to-youtube')
