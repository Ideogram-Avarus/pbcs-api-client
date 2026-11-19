"""Command line scripts, run with ``python -m pbcs_api_client <script>``.

To add one, write a module that defines a ``Script`` (see ``base.py``) and
list it here.
"""

from . import login, refresh
from .base import Script

SCRIPTS: list[Script] = [
    login.script,
    refresh.script,
]

__all__ = ["SCRIPTS", "Script"]
