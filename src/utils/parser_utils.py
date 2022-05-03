import argparse
import re

_re_pattern_value_unit = r"\s*(-?[\d.]+)\s*([a-zA-Z%]*)"
# this regex captures the following example normal(3s,1ms) with/without spaces between parenthesis and comma(s)
# it's also able to capture the sample duration specified after the distribution e.g., normal(3s,1ms) H 2ms  with/without spaces


def _parse_single_unit_value(value_str):
    """
    Convert human values in International System Units
    It accept simple value, value and unit with and without space
    :param value_str:
    :return: SI converted unit value
    """
    match = re.match(_re_pattern_value_unit, value_str)
    if match:
        value, unit = match.groups()
        if not unit:
            return float(value)
    else:
        return value_str

    # speed units
    if unit == 'kph':
        return float(value) / 3.6
    if unit == 'mph':
        return float(value) * 0.44704
    # time units
    if unit == 's':
        return float(value)
    if unit == 'ms':
        return float(value) / 1000
    if unit == 'us':
        return float(value) / 1000000
    # length unit
    if unit == 'm':
        return float(value)
    if unit == 'km':
        return float(value) * 1000
    if unit == '%':
        return float(value) / 100

    raise Exception("{} contains unknown unit {} {}".format(value_str, value, unit))