"""Unit tests for the WHO=1 messages"""


import pytest
import datetime

from OWNd.message_parser import parse_event
from OWNd.messages.who_1_lighting import OWNLightingEvent
from OWNd.const import (
    MESSAGE_TYPE_ILLUMINANCE,
    MESSAGE_TYPE_MOTION,
    MESSAGE_TYPE_MOTION_TIMEOUT,
    MESSAGE_TYPE_PIR_SENSITIVITY,
)

# TEST Events


def test_light_on_event():
    message = parse_event("*1*1*12##")

    assert message.who == 1
    assert message.where == "12"
    assert isinstance(message, OWNLightingEvent)
    assert message.entity == "1-12"
    assert message.is_on is True


def test_light_off_event():
    message = parse_event("*1*0*12##")

    assert message.who == 1
    assert message.where == "12"
    assert isinstance(message, OWNLightingEvent)
    assert message.entity == "1-12"
    assert message.is_on is False


def test_light_10_steps_brightness_event():
    message = parse_event("*1*8*12##")

    assert message.who == 1
    assert message.where == "12"
    assert isinstance(message, OWNLightingEvent)
    assert message.entity == "1-12"
    assert message.is_on is True
    assert message.brightness_preset == 8
    assert message.brightness is None


def test_light_100_steps_brightness_event():
    message = parse_event("*#1*12*1*125*2##")

    assert message.who == 1
    assert message.where == "12"
    assert isinstance(message, OWNLightingEvent)
    assert message.entity == "1-12"
    assert message.is_on is True
    assert message.brightness_preset is None
    assert message.brightness == 25
    assert message.transition == 2


def test_light_temporization_event():
    message = parse_event("*#1*12*2*1*20*35##")

    assert message.who == 1
    assert message.where == "12"
    assert isinstance(message, OWNLightingEvent)
    assert message.entity == "1-12"
    assert message.is_on is False
    assert message.timer == 4835


def test_motion_event():
    message = parse_event("*1*34*12##")

    assert message.who == 1
    assert message.where == "12"
    assert isinstance(message, OWNLightingEvent)
    assert message.entity == "1-12-motion"
    assert message.message_type == MESSAGE_TYPE_MOTION
    assert message.motion is True


def test_motion_pir_sensitivity_event():
    message = parse_event("*#1*12*5*1##")

    assert message.who == 1
    assert message.where == "12"
    assert isinstance(message, OWNLightingEvent)
    assert message.entity == "1-12-motion"
    assert message.message_type == MESSAGE_TYPE_PIR_SENSITIVITY
    assert message.pir_sensitivity == 1


def test_motion_timeout_event():
    message = parse_event("*#1*12*7*1*20*35##")

    assert message.who == 1
    assert message.where == "12"
    assert isinstance(message, OWNLightingEvent)
    assert message.entity == "1-12-motion"
    assert message.message_type == MESSAGE_TYPE_MOTION_TIMEOUT
    assert message.motion_timeout == datetime.timedelta(seconds=4835)


def test_illuminance_event():
    message = parse_event("*#1*12*6*1225##")

    assert message.who == 1
    assert message.where == "12"
    assert isinstance(message, OWNLightingEvent)
    assert message.entity == "1-12-illuminance"
    assert message.message_type == MESSAGE_TYPE_ILLUMINANCE
    assert message.illuminance == 1225


# TEST Commands
