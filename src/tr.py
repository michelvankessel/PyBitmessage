"""
Translating text
"""


import state


class translateClass(str):
    """
    This is used so that the translateText function can be used
    when we are in daemon mode and not using any QT functions.
    Inherits from str to be compatible with PyQt6 methods expecting str.
    """

    def __new__(cls, context, text):
        instance = super().__new__(cls, text)
        instance.context = context
        return instance

    def arg(self, *values):
        """Replace argument placeholders (Qt-style %1, %2, etc.)"""
        import re
        result = self
        for value in values:
            # Find %N placeholder and replace with value
            match = re.search(r'%(\d+)', result)
            if match:
                result = result.replace('%' + match.group(1), str(value), 1)
        return translateClass(self.context, result) if result != self else self


def _translate(context, text, disambiguation=None, encoding=None, n=None):

    return translateText(context, text, n)


def translateText(context, text, n=None):
    """Translate text in context"""
    try:
        enableGUI = state.enableGUI
    except AttributeError:  # inside the plugin
        enableGUI = True
    if enableGUI:
        from PyQt6 import QtCore
        if n is None:
            result = QtCore.QCoreApplication.translate(context, text)
        else:
            result = QtCore.QCoreApplication.translate(context, text, None, n)
            # PyQt6 doesn't auto-replace %n without proper .ts files
            # Manually replace %n with the count value
            result = result.replace('%n', str(n))
        # Wrap in translateClass to support .arg() chaining
        return translateClass(context, result)
    else:
        if '%' in text:
            if n is not None:
                text = text.replace('%n', str(n))
            return translateClass(context, text.replace('%', '', 1))
        return text
