# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ('icon.ico', '.'),
    ('ui/*', 'ui'),
    ('*.dll', '.'),
    ('zadig/*', 'zadig')#,
    #('web/*', 'web')
]

a = Analysis(['auto.py'],
             pathex=['.'],
             binaries=[],
             datas=added_files,
             hiddenimports=[
                "padmiss.scandrivers.fifo",
                "padmiss.scandrivers.fs",
                "padmiss.scandrivers.hid",
                "padmiss.scandrivers.usb",
                "padmiss.scandrivers.web"
             ],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Padmiss',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True , icon='icon.ico')
