"""OpenWebNet messages related to automation and lighting diagnostics (WHO=1001)"""
import re

from .base_message import OWNEvent, OWNCommand


class OWNAutomationDiagnosticCommand(OWNCommand):
    """Command messages related to diagnostics functions"""


class OWNAutomationDiagnosticEvent(OWNEvent):
    """Event messages related to diagnostics functions"""
