#!/usr/bin/env python
import logging
from typing import Optional


def get_logger(file_name: str, class_name: Optional[str] = None) -> logging.Logger:
    """Returns a logger with an appropriate name.
    Use as follows::

        logger = get_logger(__name__)

    If for example `__name__` is `telegram.ext._updater`, the logger will be named
    `telegram.ext.Updater`. If `class_name` is passed, this will result in
    `telegram.ext.<class_name>`. Useful e.g. for CamelCase class names.

    If the file name points to a utils module, the logger name will simply be `telegram(.ext)`.

    Returns:
        :class:`logging.Logger`: The logger.
    """
    parts = file_name.split("_")
    if parts[1].startswith("utils") and class_name is None:
        name = parts[0].rstrip(".")
    else:
        name = f"{parts[0]}{class_name or parts[1].capitalize()}"
    return logging.getLogger(name)
