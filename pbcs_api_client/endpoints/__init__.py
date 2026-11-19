"""Endpoint groups, one subpackage each.

Import a group's types from its subpackage, e.g.
``from pbcs_api_client.endpoints.forms import FormData``.
"""

from .base import Endpoint

__all__ = ["Endpoint"]
