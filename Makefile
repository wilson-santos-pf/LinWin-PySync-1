all: winstall

clean:
	rm -rf build sync/__pycache__ sync/*.pyc LocalboxSync-0.1a0.win32.exe LocalBoxInstaller.exe dist/*

winstall: clean  installer

installer: exe
	makensis winstall.nsis

exe:
	wine python.exe setup.py bdist_wininst
	#python setup.py bdist_wininst
	cp dist/LocalboxSync-0.1a0.win32.exe .

translatefile:
	pygettext.py -o localboxsync.pot -k lgettext sync

translate:
	msgfmt.py -o sync/locale/nl/LC_MESSAGES/localboxsync.mo localboxsync.po
