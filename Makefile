all: winstall

clean:
	rm -rf build sync/__pycache__ sync/*.pyc LocalboxSync-0.1a*.win32.exe LocalBoxInstaller.exe dist/*

winstall: clean  installer

installer: exe
	makensis winstall.nsh

exe:
	wine python.exe setup.py bdist_wininst
	#python setup.py bdist_wininst
	cp dist/LocalboxSync-0.1a*.win32.exe .

translatefile:
	pygettext.py -o localboxsync.pot -k lgettext -k translate sync

translate:
	msgfmt.py -o sync/locale/nl/LC_MESSAGES/localboxsync.mo localboxsync.po
