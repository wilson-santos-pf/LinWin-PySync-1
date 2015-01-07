# Wrapper around Python setuptools

all:
	python setup.py build

install:
	python setup.py install
	cp lox-client.desktop /usr/share/applications/.
	cp lox/gui/localbox_256.png /usr/share/icons/localbox.png

uninstall:
	rm -rf /usr/local/lib/python2.7/dist-packages/lox_client-0.1-py2.7.egg
	rm -f /usr/local/bin/lox-client
	rm -f /usr/share/applications/lox-client.desktop
	rm -f /usr/share/icons/localbox.png
