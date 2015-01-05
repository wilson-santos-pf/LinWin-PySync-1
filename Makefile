# Wrapper around Python setuptools

all:
	python setup.py build

install:
	python setup.py install
	cp lox-client.desktop $HOME/.local/share/applications

uninstall:
	rm -r /usr/local/lib/python2.7/dist-packages/lox_client-0.1-py2.7.egg
	rm /usr/local/bin/lox-client
	rm $HOME/.local/share/applications/lox-client.desktop

