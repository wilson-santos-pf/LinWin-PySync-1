Woord vooraf
====
Dit is een eerste samenraapsel van Python code van de afgelopen twee weken, afgeleid is van een eerdere in Erlang geschreven client. Reden voor overstap naar Python is betere GPG ondersteuning en ruimere beschikbaarheid van GUI libraries. Dit is met nadruk een 'work in progress'. De code is nog incompleet en werkt niet. Er zijn issues met de cache (shelve) en nog niet alle acties zijn overgenomen. Encryptie is nog niet geimplementeerd. De GUI delen zijn nog niet overgenomen. Hieronder de tekst van de README zoals bij de oorspronkelijke lox-client was opgenomen (met zoek en vervang Erlang = Python).




lox-client
=====

Notice
-----
Copyright (C) 2014. All Rights Reserved. This software is published under EUPL 1.1, see the LICENSE file in this repository for the license information.

Abstract
-----
This software is a LocalBox desktop sync client for Linux (and it can be made run on other platforms with appropriate modifications). The LocalBox server is developed by the ["Wij Delen Veilig"](http://wijdelenveilig.org) foundation. This desktop sync client adheres to the globally specified API and is tested against version 1.1.3.

Disclaimer
----
This desktop sync client does NOT offer a secure container for the files that are synchronized with a LocalBox server. Therefore the desktop sync client relies completely on the local security of the desktop. See the [end node problem](http://en.wikipedia.org/wiki/End_node_problem) for the description of the security riscs you are subject to when using this desktop sync client.

Installation
-----
The lox-client desktop sync client has some dependencies to be resolved before being able to build and install the client. On a Debian based system (like Ubuntu and Mint) the following packages are needed.

	$ sudo apt-get install \
        python-gnupg \
        python-httplib2

For installation of Python on MacOS follow the instructions on [python.org](https://www.python.org/downloads/mac-osx/). Keep with a 2.6 or 2.7 version of Python for this moment.

Download the software and extract it in a separate directory. Then build and install it.

	$ wget http://github.com/imtal/lox-client.zip
	$ unzip lox-client.zip
	$ mv lox-client-master lox-client
	$ cd lox-client
	lox-client $ make
	lox-client $ sudo make install

Remove the software again by issueing the following command.

	lox-client $ sudo make uninstall


Usage
-----
The client can be used from the command line with the following options.

	$ lox-client

	Usage: lox-client start|stop|reload|sync|status|help|...

           start  - starts the client (default when not started)
           stop   - stops the client
           config - edit the configuration file (default when alredey started)
           reload - reloads the confguration
           sync   - force a synchronization
           status - show the status of the client
           help   - this help

Without an option a usage message is shown.


Configuration
-----
The configuration is stored in the `~/.lox` directory under the filename `lox-client.conf`. This file uses the well known INI format. The general options are placed on top and for each registered host a separate heading can be used. The name of the heading is is used as the session id and  therefore needs to be unique. Headings and keys can repeated but when declarations are repeated only the last one is used. The configuration file is protected with a 'chmod 700' because the file stores user identity information. Every time the client is started the file is protected that way.

	[WijDelenVeilig]
	lox_url=https://localbox.wijdelenveilig.org/lox_api
    oauth_url=https://linkedin.com/token
	dir=~/wijdelenveilig
	username=sample_user@some.org
	password=hertzlichwilkommen
	log_level=warning
	interval=300 ; interval in seconds

	[localhost]
	lox_url=http://localhost/lox_api ; no trailing semicolon please
    oauth_url=https://localhost/lox_api/oauth2/token
	dir=~/test ; a leading tilde is replaced with $HOME
	username=admin
	password=adminpasswd
	log_level=debug ; error|warning|info|debug|traffic
	interval=180 ; interval in seconds, 0 means no automatic sync



Data
-----
The LocalBox client stores its data also in the `~/.lox` directory. In this directory a cache, data directory and log file is kept for every connection. The session id used in the configuration file is used as the name of the cache, data and logfile. The actual folders that are synced are usually static links to data folders within the config directory. Therefore changing a destination directory only results in the rename of that link so the data and synchronization state are not lost.


Concepts
----
The lox-client allows multiple sessions to synchronize folder contents with LocalBox servers. Each session is uniquely identified by a a session name, by changing this name all previous session information is deleted and a new session is created.

The desktop sync client implements two-way synchronization. A file is considered to be changed when the modified time of the file is different or the size is different. The client keeps track of the files when they are synced. When changed it can determine if a file needs to be uploaded, downloaded or deleted. Conflicts are handled automatically. When there is a conflict the actual state of the server is considered leading and the files or folders on the client are renamed and then all files or folders are merged.

The synchronization is based on a two-way sync mechanism where each session keeps track of metadata of files when they are synchronized. With this metadata it can be determined on each consecutive run whether the file is changed locally or remote. Walking through the file tree is called reconciliation, determination of the action to be taken is called resolution with a special case for conflict handling.

Reconciliation is done per directory, both file sets are joined in one list and walked through. Resolution is done by comparing the file metadata from the local stored file, from the remote stored file and from the cache containing the metadata from the last synchronization run. Comparison of metadata is currecntly done by comparing both modification date and size. A future feature can be a check on MD5 checksum locally which is bound to the version number remote.

Special cases are when a file is changed locally as well as remote, or an even more seldom case that a file is replaced by a directory with the same name. These cases are called conflicts and they are resolved by changing the name of the local file. In conflict situations it is always the local file that is renamed, the server state is considered leading.

You can recognize a conflict by a filename that ends with a `_conflict_23DE2A` like extension to the filename before the extension. When a conflict occurs, you can just delete or rename the files to get the right version in place.

Shared folders are (should be) handled in a special way. Deleting a complete folder that is a share is implemented as a revoke of that folder (check if server blocks a delete of an not owned directory). This is not yet implemented (see wihlist below) and the server allows you to delete a shered folder completely. So, please be aware of this situsaion.


Implementation
----
The desktop sync client is developed around a user space deamon that handles all communication with the LocalBox servers. The desktop sync deamon runs under the permissions of the user and synchronizes a local folder with the contents of one or more remote LocalBox accounts. The deamon is started once and can handle multiple sessions allowing multiple local folders to besynchronized. A  [desktop file](http://standards.freedesktop.org/desktop-entry-spec/latest/) is placed in `$XDG_DATA_DIRS/applications/`. By placing it in a startup folder the deamon can be started automatically, otherwise the user has to start it manually from a command line. The user space deamon is written as a Python application. The deamon uses a pid file to determine if it is already running.


Cross platform
----
Most components (Pyhton, ...) are available on several platforms like Windows, BSD, Solaris, etc. This implementaion is primarly tested under Ubuntu and Mint. Cross platform ports to MacOS or even Windows or mobile are in theory possible.

Currently, the iOS client_id and client_secret are used so to the server this desktop sync client looks like an iOS app. To avoid these kinds of masquerade appropriate id's should be specified in advance.

Wishlist
----
As this is an alpha version the wishlist is quite long. The following functionality will be implemented in a later stage.
* proper handling of shared folders (revoke invitiation when deleted at top level)
* sync of encrypted folders
* use alternative for httplib for better asynchronous handling of large files (now done through memory)
* allow for partial downloads/uploads (if the server supports it)
* desktop notification (via DBus)
* group system messages in logger in order to send notifications with compressed information (i.e. "There are 3 updated files")
* systray icon (both freedesktop.org and Unity specs if possible)
* GUI (dialogs) for configuration and invitation handling
* use of the system keyring for storing passwords and keys
* change icons and emblems via gvs
* add file comparison based on MD5 checksum local bound to the version number remote
* allow a directory to be published using the context menu

Authors
----
Tjeerd van der Laan
