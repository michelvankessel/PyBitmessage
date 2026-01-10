# -*- coding: utf-8 -*-
"""
Operating with plugins - Modern implementation using importlib.metadata

This eliminates the pkg_resources deprecation warning while maintaining
full functionality with modern Python standards.
"""

import logging


logger = logging.getLogger("default")


def get_plugins(group, point="", name=None, fallback=None):
    """
    Iterate through plugins (connect_plugin attribute of entry point)
    which name starts with point or equals to name.
    If fallback kwarg specified, plugin with that name yield last.

    :param str group: plugin group
    :param str point: plugin name prefix
    :param name: exact plugin name
    :param fallback: fallback plugin name
    :return: generator of plugin objects
    """
    _fallback = None  # Initialize _fallback to avoid NameError

    # Try modern importlib.metadata first (Python 3.8+)
    try:
        import importlib.metadata as metadata

        # Get entry points for the specific group
        group_name = "bitmessage." + group

        # Get all entry points and filter for our group
        try:
            all_eps = metadata.entry_points()

            # Filter for our specific group
            if hasattr(all_eps, "select"):  # Python 3.10+
                group_eps = all_eps.select(group=group_name)
            else:
                # Manual filtering for older versions
                group_eps = [
                    ep for ep in all_eps if getattr(ep, "group", None) == group_name
                ]

            for ep in group_eps:
                if name and ep.name == name or not point or ep.name.startswith(point):
                    try:
                        plugin_class = ep.load()
                        if hasattr(plugin_class, "connect_plugin"):
                            plugin = plugin_class.connect_plugin
                            if ep.name == fallback:
                                _fallback = plugin
                            else:
                                yield plugin
                        else:
                            logger.debug(
                                "Plugin %s missing connect_plugin attribute", ep.name
                            )
                    except Exception as e:
                        logger.debug(
                            "Problem while loading %s: %s", ep.name, e, exc_info=True
                        )
                        continue

        except Exception as e:
            logger.debug("Error accessing entry points: %s", e)

    except ImportError:
        # Fallback to pkg_resources for older Python versions
        logger.debug("importlib.metadata not available, falling back to pkg_resources")

        try:
            import pkg_resources

            for ep in pkg_resources.iter_entry_points("bitmessage." + group):
                if name and ep.name == name or not point or ep.name.startswith(point):
                    try:
                        plugin = ep.load().connect_plugin
                        if ep.name == fallback:
                            _fallback = plugin
                        else:
                            yield plugin
                    except (
                        AttributeError,
                        ImportError,
                        ValueError,
                        pkg_resources.DistributionNotFound,
                        pkg_resources.UnknownExtra,
                    ):
                        logger.debug("Problem while loading %s", ep.name, exc_info=True)
                        continue
        except ImportError:
            logger.warning("No plugin system available")

    if _fallback:
        yield _fallback


def get_plugin(*args, **kwargs):
    """
    Return first available plugin from get_plugins if any.
    """
    for plugin in get_plugins(*args, **kwargs):
        return plugin
    return None
