import logging
from importlib import import_module
from pathlib import Path
from typing import Any

logger = logging.getLogger("default")


paths: Any
try:
    from pybitmessage import paths
except ImportError:
    paths = None


def constructObject(data):
    """Constructing an object"""
    whitelist = ["message"]
    if data[""] not in whitelist:
        return None
    try:
        classBase = getattr(
            import_module(".{}".format(data[""]), __name__), data[""].title()
        )
    except (NameError, AttributeError, ValueError, ImportError):
        logger.error(
            'Don\'t know how to handle message type: "%s"', data[""], exc_info=True
        )
        return None
    except Exception:
        logger.error(
            'Don\'t know how to handle message type: "%s"', data[""], exc_info=True
        )
        return None

    try:
        returnObj = classBase()
        returnObj.decode(data)
    except KeyError as e:
        logger.error("Missing mandatory key %s", e)
        return None
    except Exception:
        logger.error("classBase fail", exc_info=True)
        return None
    else:
        return returnObj


if paths and paths.frozen is not None:
    import_module(".message", __name__)
    import_module(".vote", __name__)
else:
    for mod_path in Path(__file__).parent.iterdir():
        if mod_path.name == "__init__.py":
            continue
        if mod_path.suffix != ".py":
            continue
        mod = mod_path.name
        try:
            import_module(".{}".format(mod_path.stem), __name__)
        except ImportError:
            logger.error("Error importing %s", mod, exc_info=True)
        else:
            logger.debug("Imported message type module %s", mod)
