# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['env/Lib/site-packages/shiboken6', '.'],
             binaries=[('env/Lib/site-packages/PySide6/plugins/platforms/*', 'platforms'),
                       ('env/Lib/site-packages/PySide6/plugins/styles/*', 'styles')],
             datas=[('ui/*.ui', 'ui')],
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
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='songs-to-youtube')
