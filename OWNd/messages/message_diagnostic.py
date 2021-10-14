"""This module contains OpenWebNet messages related to diagnostics"""
import re

from ..message import OWNMessage, OWNEvent, OWNCommand


class OWNDiagnosticCommand(OWNCommand):
    """Command messages related to diagnostics functions"""


class OWNDiagnosticEvent(OWNEvent):
    """Event messages related to diagnostics functions"""
