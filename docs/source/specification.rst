Specification
*************

Client Side Encryption
======================

The user's files are download and stored encrypted on disk.
Because the files eventually will be opened they have to be decrypted somehow.
When the files are downloaded from the server a custom file extension (.lox) is added to the files.
The .lox file extension is understood by the LocalBox client.

.. image:: ../_diagrams/encryption_client_side_download.*

When the user wants to open the encrypted files, the operating system asks the LocalBox client to open them.
The client decrypts them (asking for the passphrase if necessary).
Once decrypted the client gives control to the operating system to open the decrypted files.

.. image:: ../_diagrams/encryption_client_side_usage.*

The client keeps track of all the decrypted files.
Upon application exit the client will delete these files.
The user has the option to delete these files at any time:

.. image:: ../_static/usermanual/localbox-delete-decrypted.*
