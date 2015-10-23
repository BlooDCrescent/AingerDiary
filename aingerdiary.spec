# -*- mode: python -*-

block_cipher = None
import kivy
from kivy.tools.packaging.pyinstaller_hooks import get_hooks
import os

a = Analysis(['aingerdiary.py'],
             pathex=['C:\\Users\\Sergey\\PyCharmProjects\\AingerDiary'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             excludes=[],
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher,
			 **get_hooks())
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='aingerdiary',
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe, Tree('./'), Tree([f for f in os.environ.get('KIVY_SDL2_PATH', '').split(';') if 'bin' in f][0]),
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='aingerdiary')
