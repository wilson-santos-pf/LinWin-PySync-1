**************************
Frequently Asked Questions
**************************

Why wxPython3.0 and not wxPython2.8?
====================================

The ToolBar class of version 2.8 misses some important methods like ``GetToolByPos`` and ``AddStretchableSpace``.

More importantly, the layout gets all messed up:

.. image:: ../_static/wx30_vs_wx28.jpg


Password and Passphrase? What's the difference?
===============================================

When you configure a new LocalBox you will be prompted for the credentials that authenticate you in the system.
These credentials are your username and password. They will be only asked one per LocalBox configuration.
In the following step you will be prompted for the passphrase. This passhprase will protect you private key and will
be prompted every time you open the application.