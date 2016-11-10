Contributions
*************

Start Developing
================

.. code:: bash

    # get the code
    git clone https://github.com/2EK/LinWin-PySync.git
    # switch to the develop branch
    git checkout develop
    # compile the translations
    make translations

Solving a bug? Create your branch with (replace <ISSUE_NUMBER> with the appropriate number):

.. code:: bash

    git flow bugfix start LOXGUI-<ISSUE_NUMBER>

Creating a new feature ? Create your branch with (replace <ISSUE_NUMBER> with the appropriate number):

.. code:: bash

    git flow feature start LOXGUI-<ISSUE_NUMBER>


Documentation
=============

Want to contribute your knowledge to the cause? Cool.

.. code:: bash

    # get the code
    git clone https://github.com/2EK/LinWin-PySync.git

    mkdir LinWin-PySync-docs
    cd LinWin-PySync-docs

    # clone the repo into a dir called html:
    git clone https://github.com/2EK/LinWin-PySync.git html
    cd html

    #
    git checkout gh-pages
    git symbolic-ref HEAD refs/heads/gh-pages
    rm .git/index
    git clean -fdx

    # compile the documentation as HTML
    cd ../LinWin-PySync
    make html

Reference: https://daler.github.io/sphinxdoc-test/includeme.html



Translations
============

Creating a new translation
--------------------------

Install Poedit

.. code:: bash

    sudo apt-get install poedit

Create POT file:

.. code:: bash

    make translatefile

Create translation from POT:

.. image:: ../_static/create_translation.*

Open POT:

.. image:: ../_static/open_pot.*

Choose language:

.. image:: ../_static/pot_choose_language.*

Translate the text and save PO in ``./translations``:

.. image:: ../_static/translations_save_po.*

Compile to MO:

.. code:: bash

    make translations


Updating a translation
----------------------

Lets contemplate the scenario where the developers added more strings / messages to the application. Now we need to
make a translation for these new strings.


Create POT file again:

.. code:: bash

    make translatefile

Open your previous PO file (located in ``./translations``) and update it from the new POT.

.. image:: ../_static/translations_update_from_pot.*

The new strings are added to the PO file. Translate them, save and compile:

.. code:: bash

    make translations


Adding translation to the application
-------------------------------------

So your PO file is ready to use, but how?

Add the name of the language in upper case (it should match ``[A-Z_]+``) as the key of ``LANGUAGES`` and use the name of
the PO file (without the extension) as the value:

.. image:: ../_static/translations_language_py.*

After restarting the application the new language is displayed as a choice:

.. image:: ../_static/translations_app.*
