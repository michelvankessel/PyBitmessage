# -*- coding: utf-8 -*-
"""
Sound notification plugin using gstreamer
"""
import gi


_player = None


def connect_plugin(sound_file):
    """Entry point for sound file"""
    global _player
    if _player is None:
        gi.require_version('Gst', '1.0')
        from gi.repository import Gst
        Gst.init(None)
        _player = Gst.ElementFactory.make("playbin", "player")

    from gi.repository import Gst
    _player.set_state(Gst.State.NULL)
    _player.set_property("uri", "file://" + sound_file)
    _player.set_state(Gst.State.PLAYING)
