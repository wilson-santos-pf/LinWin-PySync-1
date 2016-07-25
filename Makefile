all: winstall

sync/version.py:
	echo VERSION=`echo "from subprocess import check_output; print len([elem for elem in check_output(['git', 'log']).split('\n') if elem.startswith('commit ')])" | python` >> sync/version.py

clean:
	rm -rf build sync/__pycache__ sync/*.pyc LocalBoxSync-0.1a*.win32.exe LocalBoxInstaller.exe dist/* gnupg.pyc sync/version.py

winstall: clean  installer

installer: exe
	makensis winstall.nsh

exe: sync/version.py
	wine python.exe setup.py bdist_wininst
	#python setup.py bdist_wininst
	cp dist/LocalBoxSync-0.1a*.win32.exe .

translatefile:
	pygettext.py -o localboxsync.pot -k lgettext -k translate sync

translate:
	msgfmt.py -o sync/locale/nl/LC_MESSAGES/localboxsync.mo localboxsync.po
