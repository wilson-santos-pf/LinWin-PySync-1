"""
LocalBox synchronization client.
"""

from sync import language
from sync.controllers.preferences_ctrl import PreferencesController
from sync.defaults import SYNCINI_PATH, LOG_PATH, APPDIR

language.set_language(PreferencesController().get_language_abbr())
