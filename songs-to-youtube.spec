# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['songs_to_youtube/main.py'],
             pathex=['.'],
             binaries=[],
             datas=[('songs_to_youtube/ui/*.ui', 'ui'),
                    ('songs_to_youtube/config/*.ini', 'config'),
                    ('songs_to_youtube/commands/concat/*.command', 'commands/concat'),
                    ('songs_to_youtube/commands/render/*.command', 'commands/render'),
                    ('songs_to_youtube/image/*', 'image')],
             hookspath=[],
             hooksconfig={},
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
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='songs-to-youtube',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='songs_to_youtube/image/icon.ico')
