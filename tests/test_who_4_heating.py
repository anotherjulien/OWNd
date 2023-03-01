"""Unit tests for the WHO=2 messages"""


from OWNd.const import (
    CLIMATE_MODE_AUTO,
    CLIMATE_MODE_COOL,
    CLIMATE_MODE_HEAT,
    CLIMATE_MODE_OFF,
    MESSAGE_TYPE_ACTION,
    MESSAGE_TYPE_LOCAL_OFFSET,
    MESSAGE_TYPE_LOCAL_TARGET_TEMPERATURE,
    MESSAGE_TYPE_MAIN_HUMIDITY,
    MESSAGE_TYPE_MAIN_TEMPERATURE,
    MESSAGE_TYPE_MODE,
    MESSAGE_TYPE_MODE_TARGET,
    MESSAGE_TYPE_SECONDARY_TEMPERATURE,
    MESSAGE_TYPE_TARGET_TEMPERATURE,
)
from OWNd.message_parser import parse_event
from OWNd.messages.who_4_heating import OWNHeatingEvent
import pytest

# TEST Events


def test_main_temperature_event():
    message = parse_event("*#4*12*0*0123##")

    assert message.who == 4
    assert message.where == "12"
    assert isinstance(message, OWNHeatingEvent)
    assert message.entity == "4-12"
    assert message.zone == 12
    assert message.sensor is None
    assert message.message_type == MESSAGE_TYPE_MAIN_TEMPERATURE
    assert message.main_temperature == 12.3


def test_secondary_temperature_event():
    message = parse_event("*#4*112*0*0123##")

    assert message.who == 4
    assert message.where == "112"
    assert isinstance(message, OWNHeatingEvent)
    assert message.entity == "4-112"
    assert message.zone == 12
    assert message.sensor == 1
    assert message.message_type == MESSAGE_TYPE_SECONDARY_TEMPERATURE
    assert message.secondary_temperature == (1, 12.3)


def test_main_humidity_event():
    message = parse_event("*#4*12*60*55##")

    assert message.who == 4
    assert message.where == "12"
    assert isinstance(message, OWNHeatingEvent)
    assert message.entity == "4-12"
    assert message.zone == 12
    assert message.message_type == MESSAGE_TYPE_MAIN_HUMIDITY
    assert message.main_humidity == 55.0


def test_target_temperature_event():
    message = parse_event("*#4*12*14*0225*3##")

    assert message.who == 4
    assert message.where == "12"
    assert isinstance(message, OWNHeatingEvent)
    assert message.entity == "4-12"
    assert message.zone == 12
    assert message.message_type == MESSAGE_TYPE_TARGET_TEMPERATURE
    assert message.set_temperature == 22.5


def test_no_local_offset_event():
    message = parse_event("*#4*12*13*00##")

    assert message.who == 4
    assert message.where == "12"
    assert isinstance(message, OWNHeatingEvent)
    assert message.entity == "4-12"
    assert message.zone == 12
    assert message.message_type == MESSAGE_TYPE_LOCAL_OFFSET
    assert message.local_offset == 0


def test_positive_local_offset_event():
    message = parse_event("*#4*12*13*02##")

    assert message.who == 4
    assert message.where == "12"
    assert isinstance(message, OWNHeatingEvent)
    assert message.entity == "4-12"
    assert message.zone == 12
    assert message.message_type == MESSAGE_TYPE_LOCAL_OFFSET
    assert message.local_offset == 2


def test_negative_local_offset_event():
    message = parse_event("*#4*12*13*12##")

    assert message.who == 4
    assert message.where == "12"
    assert isinstance(message, OWNHeatingEvent)
    assert message.entity == "4-12"
    assert message.zone == 12
    assert message.message_type == MESSAGE_TYPE_LOCAL_OFFSET
    assert message.local_offset == -2


def test_local_target_temperature_event():
    message = parse_event("*#4*12*12*0225*3##")

    assert message.who == 4
    assert message.where == "12"
    assert isinstance(message, OWNHeatingEvent)
    assert message.entity == "4-12"
    assert message.zone == 12
    assert message.message_type == MESSAGE_TYPE_LOCAL_TARGET_TEMPERATURE
    assert message.local_set_temperature == 22.5


def test_auto_mode_event():
    message = parse_event("*4*311*#12##")

    assert message.who == 4
    assert message.where == "#12"
    assert isinstance(message, OWNHeatingEvent)
    assert message.entity == "4-12"
    assert message.zone == 12
    assert message.message_type == MESSAGE_TYPE_MODE
    assert message.mode == CLIMATE_MODE_AUTO
