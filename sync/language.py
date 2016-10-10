import gettext

from sync.defaults import LOCALE_PATH

LANGUAGES = {
    'ENGLISH': 'en',
    'DUTCH': 'nl'
}

def set_language(lang):
    """
    Gets the translation from the MO files
    :param lang: should be a string like 'en', 'nl, etc
    :return:
    """
    translation = gettext.translation('localboxsync', localedir=LOCALE_PATH, languages=[lang])
    translation.install()