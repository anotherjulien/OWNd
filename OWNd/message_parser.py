"""Module containing the entry point for message parsing/sorting"""

from typing import Optional

from .const import (
    PATTERN_ACK,
    PATTERN_NACK,
    PATTERN_COMMAND_SESSION,
    PATTERN_EVENT_SESSION,
    PATTERN_NONCE,
    PATTERN_SHA,
    PATTERN_STATUS,
    PATTERN_STATUS_REQUEST,
    PATTERN_DIMENSION_REQUEST,
    PATTERN_DIMENSION_REQUEST_REPLY,
    PATTERN_DIMENSION_WRITING,
)

from .messages.base_message import OWNMessage, OWNEvent, OWNCommand, OWNSignaling
from .messages.who_0_scenario import OWNScenarioEvent
from .messages.who_1_lighting import OWNLightingEvent, OWNLightingCommand
from .messages.who_2_automation import OWNAutomationEvent, OWNAutomationCommand
from .messages.who_4_heating import OWNHeatingEvent, OWNHeatingCommand
from .messages.who_5_burglar_alarm import OWNAlarmEvent
from .messages.who_9_auxiliaries import OWNAuxEvent
from .messages.who_13_gateway import OWNGatewayEvent, OWNGatewayCommand
from .messages.who_15_cen import OWNCENEvent
from .messages.who_17_scene import OWNSceneEvent
from .messages.who_18_energy import OWNEnergyEvent, OWNEnergyCommand
from .messages.who_25_cen_plus import OWNCENPlusEvent
from .messages.who_25_dry_contact import OWNDryContactEvent, OWNDryContactCommand


def parse(data: str) -> Optional[OWNMessage]:
    if (
        PATTERN_ACK.match(data)
        or PATTERN_NACK.match(data)
        or PATTERN_COMMAND_SESSION.match(data)
        or PATTERN_EVENT_SESSION.match(data)
        or PATTERN_NONCE.match(data)
        or PATTERN_SHA.match(data)
    ):
        return OWNSignaling(data)
    elif PATTERN_STATUS.match(data) or PATTERN_DIMENSION_REQUEST_REPLY.match(data):
        return parse_event(data)
    elif (
        PATTERN_STATUS_REQUEST.match(data)
        or PATTERN_DIMENSION_REQUEST.match(data)
        or PATTERN_DIMENSION_WRITING.match(data)
    ):
        return parse_command(data)
    else:
        return None


def parse_event(data: str) -> OWNEvent:

    event_message = OWNEvent(data)

    if event_message.who == 0:
        return OWNScenarioEvent(data)
    elif event_message.who == 1:
        return OWNLightingEvent(event_message)
    elif event_message.who == 2:
        return OWNAutomationEvent(event_message)
    elif event_message.who == 4:
        return OWNHeatingEvent(event_message)
    elif event_message.who == 5:
        return OWNAlarmEvent(data)
    elif event_message.who == 9:
        return OWNAuxEvent(data)
    elif event_message.who == 13:
        return OWNGatewayEvent(data)
    elif event_message.who == 15:
        return OWNCENEvent(data)
    elif event_message.who == 17:
        return OWNSceneEvent(data)
    elif event_message.who == 18:
        return OWNEnergyEvent(data)
    elif event_message.who == 25:
        if event_message.where.startswith("2"):
            return OWNCENPlusEvent(data)
        elif event_message.where.startswith("3"):
            return OWNDryContactEvent(data)

    return event_message


def parse_command(data: str) -> OWNCommand:

    command_message = OWNCommand(data)

    if command_message.who == 1:
        return OWNLightingCommand(data)
    elif command_message.who == 2:
        return OWNAutomationCommand(data)
    elif command_message.who == 4:
        return OWNHeatingCommand(data)
    elif command_message.who == 13:
        return OWNGatewayCommand(data)
    elif command_message.who == 18:
        return OWNEnergyCommand(data)
    elif command_message.who == 25:
        if command_message.where.startswith("2"):
            return OWNCommand(data)
        elif command_message.where.startswith("3"):
            return OWNDryContactCommand(data)

    return command_message
