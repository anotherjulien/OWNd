"""Constants related to different OpenWebNet message types"""

import re


# Message patterns
## Signaling messages
PATTERN_ACK = re.compile(r"^\*#\*1##$")  #  *#*1##
PATTERN_NACK = re.compile(r"^\*#\*0##$")  #  *#*0##
PATTERN_COMMAND_SESSION = re.compile(r"^\*99\*0##$")  #  *99*0##
PATTERN_EVENT_SESSION = re.compile(r"^\*99\*1##$")  #  *99*1##
PATTERN_NONCE = re.compile(r"^\*#(\d+)##$")  #  *#123456789##
PATTERN_SHA = re.compile(r"^\*98\*(\d)##$")  #  *98*SHA##
## Status messages
PATTERN_STATUS = re.compile(
    r"^\*(?P<who>\d+)\*(?P<what>\d+)(?P<what_param>(?:#\d+)*)\*(?P<where>\*|#?\d+)(?P<where_param>(?:#\d+)*)##$"  # pylint: disable=line-too-long
)  #  *WHO*WHAT*WHERE##
PATTERN_STATUS_REQUEST = re.compile(
    r"^\*#(?P<who>\d+)\*(?P<where>#?\d+)(?P<where_param>(?:#\d+)*)##$"
)  #  *#WHO*WHERE
## Dimension messages
PATTERN_DIMENSION_WRITING = re.compile(
    r"^\*#(?P<who>\d+)\*(?P<where>#?\d+)?(?P<where_param>(?:#\d+)*)?\*#(?P<dimension>\d+)(?P<dimension_param>(?:#\d+)*)?(?P<dimension_value>(?:\*\d+)+)##$"  # pylint: disable=line-too-long
)  #  *#WHO*WHERE*#DIMENSION*VAL1*VALn##
PATTERN_DIMENSION_REQUEST = re.compile(
    r"^\*#(?P<who>\d+)\*(?P<where>#?\d+)?(?P<where_param>(?:#\d+)*)?\*(?P<dimension>\d+)##$"
)  #  *#WHO*WHERE*DIMENSION##
PATTERN_DIMENSION_REQUEST_REPLY = re.compile(
    r"^\*#(?P<who>\d+)\*(?P<where>#?\d+)?(?P<where_param>(?:#\d+)*)?\*(?P<dimension>\d+)(?P<dimension_param>(?:#\d+)*)?(?P<dimension_value>(?:\*\d+)+)##$"  # pylint: disable=line-too-long
)  #  *#WHO*WHERE*DIMENSION*VAL1*VALn##

# Energy message types
MESSAGE_TYPE_ACTIVE_POWER = "active_power"
MESSAGE_TYPE_ENERGY_TOTALIZER = "energy_totalizer"
MESSAGE_TYPE_HOURLY_CONSUMPTION = "hourly_consumption"
MESSAGE_TYPE_DAILY_CONSUMPTION = "daily_consumption"
MESSAGE_TYPE_MONTHLY_CONSUMPTION = "monthly_consumption"
MESSAGE_TYPE_CURRENT_DAY_CONSUMPTION = "current_day_partial_consumption"
MESSAGE_TYPE_CURRENT_MONTH_CONSUMPTION = "current_month_partial_consumption"

# Heating message types
MESSAGE_TYPE_MAIN_TEMPERATURE = "main_temperature"
MESSAGE_TYPE_MAIN_HUMIDITY = "main_humidity"
MESSAGE_TYPE_SECONDARY_TEMPERATURE = "secondary_temperature"
MESSAGE_TYPE_TARGET_TEMPERATURE = "target_temperature"
MESSAGE_TYPE_LOCAL_OFFSET = "local_offset"
MESSAGE_TYPE_LOCAL_TARGET_TEMPERATURE = "local_targer_temperature"
MESSAGE_TYPE_MODE = "hvac_mode"
MESSAGE_TYPE_MODE_TARGET = "hvac_mode_target"
MESSAGE_TYPE_ACTION = "hvac_action"

# Motion and illuminance message types
MESSAGE_TYPE_MOTION = "motion_detected"
MESSAGE_TYPE_PIR_SENSITIVITY = "pir_sensitivity"
MESSAGE_TYPE_ILLUMINANCE = "illuminance_value"
MESSAGE_TYPE_MOTION_TIMEOUT = "motion_timeout"

CLIMATE_MODE_OFF = "off"
CLIMATE_MODE_HEAT = "heat"
CLIMATE_MODE_COOL = "cool"
CLIMATE_MODE_AUTO = "auto"

PIR_SENSITIVITY_MAPPING = ["low", "medium", "high", "very high"]
