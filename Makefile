all: winstall

sync/version.py:
	echo VERSION=\'`cat VERSION``git log | grep -c ^commit`\' >> sync/version.py

clean:
	find . -name "*.pyc" -exec rm {} \;
	rm -rf build sync/__pycache__ LocalBoxSync-0.1a*.win32.exe LocalBoxInstaller.exe dist/* sync/version.py

winstall: clean  installer

installer: exe
	makensis winstall.nsh

exe: sync/version.py
	wine python.exe setup.py bdist_wininst
	#python setup.py bdist_wininst
	cp dist/LocalBoxSync-0.1a*.win32.exe .

translatefile:
	pygettext -o localboxsync.pot -k lgettext -k translate sync

translate:
	msgfmt.py -o sync/locale/nl/LC_MESSAGES/localboxsync.mo localboxsync.po
