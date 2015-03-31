# Wrapper around Python setuptools

all:
	python setup.py build

locale:
	xgettext --language=Python --keyword=_ --output=po/lox-client.pot `find . -name "*.py"`
	msginit --no-translator --input=po/lox-client.pot --output-file=po/nl.po --locale=nl
	msginit --no-translator --input=po/lox-client.pot --output-file=po/fy.po --locale=fy

clean:
	find . -name "*.pyc" -type f -delete

install:
	python setup.py install
	cp lox-client.desktop /usr/share/applications/.
	cp lox/gui/localbox_256.png /usr/share/icons/localbox.png

uninstall:
	rm -rf /usr/local/lib/python2.7/dist-packages/lox_client-0.1-py2.7.egg
	rm -f /usr/local/bin/lox-client
	rm -f /usr/share/applications/lox-client.desktop
	rm -f /usr/share/icons/localbox.png

