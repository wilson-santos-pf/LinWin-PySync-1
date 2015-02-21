lox-client
=====

Notice
-----
Copyright (C) 2014. This software is published under EUPL 1.1, see the LICENSE file in this repository for the license information.

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
        python-httplib2 \
        python-gnupg \
        haveged

The GUI has some additional dependencies:

    $ sudo apt-get install \
        python-appindicator \
        python-notify

For installation of Python on MacOS follow the instructions on [python.org](https://www.python.org/downloads/mac-osx/). Keep with a 2.6 or 2.7 version of Python for this moment.

Download the software and extract it in a separate directory. There is n

    $ wget https://github.com/2EK/Linux-Sync/archive/master.zip
    $ unzip Linux-Sync-master.zip
    $ mv Linux-Sync-master Linux-Sync
    $ cd Linux-Sync
    Linux-Sync $ make
    Linux-Sync $ sudo make install

Usage
-----
The client can be used from the command line with the following options.

    $ lox-client

    Usage: lox-client start|stop|reload|sync|status|help|...

    $ lox-client help

    LocalBox client: desktop sync version 0.1

       Usage: lox-client [command]

           status       - show the status of the client
           run          - run in foreground (interactive)
           help         - show this help
           stop         - stops the client
           invitations  - show invitations
           start        - starts the client
           restart      - reloads the confguration


Without an option a usage message is shown. Use the 'run' command to test your configuration from the console.


Configuration
-----
The configuration is stored in the `~/.lox` directory under the filename `lox-client.conf`. This file uses the well known INI format. The general options are placed on top and for each registered host a separate heading can be used. The name of the heading is is used as the session id and  therefore needs to be unique. Headings and keys can repeated but when declarations are repeated only the last one is used. The configuration file is protected with a 'chmod 700' because the file stores user identity information. Every time the client is started the file is protected that way.

    [WijDelenVeilig]
    lox_url=https://localbox.wijdelenveilig.org
    local_dir=~/wijdelenveilig
    auth_type=localbox
    username=sample_user@some.org
    password=hertzlichwilkommen
    log_level=warning
    interval=300 ; interval in seconds

    [localhost]
    lox_url=http://localhost ; no trailing slash
    local_dir=~/test ; a leading tilde is replaced with $HOME
    auth_type=localbox
    username=admin
    password=adminpasswd
    log_level=debug ; error|warning|info|debug|traffic
    interval=180 ; interval in seconds, 0 means no automatic sync



Data
-----
The LocalBox client stores its data also in the `~/.lox` directory. In this directory a cache and log file is kept for every connection. The session id used in the configuration file is used as the name of the cache, data and logfile. The actual folders that are synced are usually static links to data folders within the config directory. Therefore changing a destination directory only results in the rename of that link so the data and synchronization state are not lost.


Concepts
----
The lox-client allows multiple sessions to synchronize folder contents with LocalBox servers. Each session is uniquely identified by a a session name, by changing this name all previous session information is deleted and a new session is created.

The desktop sync client implements two-way synchronization. A file is considered to be changed when the modified time of the file is different or the size is different. The client keeps track of the files when they are synced. When changed it can determine if a file needs to be uploaded, downloaded or deleted. Conflicts are handled automatically. When there is a conflict the actual state of the server is considered leading and the files or folders on the client are renamed and then all files or folders are merged.

Reconciliation is done per directory, both file sets are joined in one list and walked through. Resolution is done by comparing the file metadata from the local stored file, from the remote stored file and from the cache containing the metadata from the last synchronization run. Comparison of metadata is currecntly done by comparing both modification date and size. A future feature can be a check on MD5 checksum locally which is bound to the version number remote.

Special cases are when a file is changed locally as well as remote, or an even more seldom case that a file is replaced by a directory with the same name. These cases are called conflicts and they are resolved by changing the name of the local file. In conflict situations it is always the local file that is renamed, the server state is considered leading.

You can recognize a conflict by a filename that ends with a `_conflict_23DE2A` like suffix to the filename before the extension. When a conflict occurs, you can just delete or rename the files to get the right version in place.

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
* use pycurl for better asynchronous handling of large files
* allow for partial downloads/uploads (if the server supports it)
* group system messages in logger in order to send notifications with compressed information (i.e. "There are 3 updated files")
* use of the system keyring for storing passwords and keys
* change icons and emblems via gvfs
* add file comparison based on MD5 checksum local bound to the version number remote
* allow a directory to be published using the context menu

Authors
----
Tjeerd van der Laan
