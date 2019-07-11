# -*- mode: python -*-

block_cipher = None

added_files = [
	( 'config-window.ui', '.' ),
	( 'device-config-widget.ui', '.' ),
	( 'scanner-config-widget.ui', '.' ),
	( 'main-window.ui', '.' ),
	( 'libusb-1.0.dll', '.' ),
	( 'icon.ico', '.' ),
	( 'zadig/zadig.ini', 'zadig/' ),
	( 'zadig/zadig.exe', 'zadig/' ),
]

a = Analysis(['gui.py'],
             pathex=['C:\\dev\\padmiss-daemon'],
             binaries=[],
             datas=added_files,
             hiddenimports=[],
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
          runtime_tmpdir=None,
          console=False,
		  icon='C:\\dev\\padmiss-daemon\\icon.ico')
