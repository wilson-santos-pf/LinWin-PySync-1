import gtk

import gettext
_ = gettext.gettext

INFO = gtk.MESSAGE_INFO
ERROR = gtk.MESSAGE_ERROR

def messagebox(icon, message):
    m = gtk.MessageDialog(None,
            gtk.DIALOG_DESTROY_WITH_PARENT, icon,
            gtk.BUTTONS_CLOSE, message)
    result = m.run()
    m.destroy()
    return result

