# -*- coding: utf-8 -*-
"""
Notification plugin using notify2
"""

import gi


_notification = None


def connect_plugin(title, subtitle, category, _, icon):
    """Plugin for notify2"""
    global _notification
    if _notification is None:
        gi.require_version('Notify', '0.7')
        from gi.repository import Notify
        Notify.init('pybitmessage')
        _notification = Notify.Notification.new("Init", "Init")

    if not icon:
        icon = 'mail-message-new' if category == 2 else 'pybitmessage'
    _notification.update(title, subtitle, icon)
    _notification.show()
