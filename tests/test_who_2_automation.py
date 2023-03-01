"""Unit tests for the WHO=2 messages"""


import pytest

from OWNd.message_parser import parse_event
from OWNd.messages.who_2_automation import OWNAutomationEvent

# TEST Events


def test_cover_stop_event():
    message = parse_event("*2*0*12##")

    assert message.who == 2
    assert message.where == "12"
    assert isinstance(message, OWNAutomationEvent)
    assert message.entity == "2-12"
    assert message.is_opening is False
    assert message.is_closing is False


def test_cover_up_event():
    message = parse_event("*2*1*12##")

    assert message.who == 2
    assert message.where == "12"
    assert isinstance(message, OWNAutomationEvent)
    assert message.entity == "2-12"
    assert message.is_opening is True
    assert message.is_closing is False
    assert message.is_closed is None


def test_cover_down_event():
    message = parse_event("*2*2*12##")

    assert message.who == 2
    assert message.where == "12"
    assert isinstance(message, OWNAutomationEvent)
    assert message.entity == "2-12"
    assert message.is_opening is False
    assert message.is_closing is True
    assert message.is_closed is None


def test_advanced_cover_closed_event():
    message = parse_event("*#2*12*10*10*0*001*0##")

    assert message.who == 2
    assert message.where == "12"
    assert isinstance(message, OWNAutomationEvent)
    assert message.entity == "2-12"
    assert message.is_opening is False
    assert message.is_closing is False
    assert message.is_closed is True


def test_advanced_cover_stop_event():
    message = parse_event("*#2*12*10*10*50*001*0##")

    assert message.who == 2
    assert message.where == "12"
    assert isinstance(message, OWNAutomationEvent)
    assert message.entity == "2-12"
    assert message.is_opening is False
    assert message.is_closing is False
    assert message.is_closed is False
    assert message.current_position == 50


def test_advanced_cover_open_event():
    message = parse_event("*2*11#10#001*12##")

    assert message.who == 2
    assert message.where == "12"
    assert isinstance(message, OWNAutomationEvent)
    assert message.entity == "2-12"
    assert message.is_opening is True
    assert message.is_closing is False
    assert message.is_closed is False


def test_advanced_cover_close_event():
    message = parse_event("*2*12#10#001*12##")

    assert message.who == 2
    assert message.where == "12"
    assert isinstance(message, OWNAutomationEvent)
    assert message.entity == "2-12"
    assert message.is_opening is False
    assert message.is_closing is True
    assert message.is_closed is False
