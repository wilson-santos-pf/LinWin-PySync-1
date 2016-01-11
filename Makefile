clean:
	rm -rf build sync/__pycache__ sync/*.pyc LocalboxSync-0.1a0.win32.exe LocalBoxInstaller.exe dist/*

all: winstall

winstall: clean  installer

installer: exe
	makensis winstall.nsis

exe:
	wine python.exe setup.py bdist_wininst
	cp dist/LocalboxSync-0.1a0.win32.exe .

	
