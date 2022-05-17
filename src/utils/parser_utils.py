import argparse
import re

_re_pattern_value_unit = r"\s*(-?[\d.]+)\s*([a-zA-Z%]*)"
# this regex captures the following example normal(3s,1ms) with/without spaces between parenthesis and comma(s)
# it's also able to capture the sample duration specified after the distribution e.g., normal(3s,1ms) H 2ms  with/without spaces
_re_pattern_compact_distribution = re.compile(
    r'^(?P<family>[a-z]+\b)\s*\(\s*(?P<args>-?\d*\.?\d+\s*[a-z]*\b(\s*,\s*-?\d*\.?\d+\s*[a-z]*\b)*)\s*\)\s*(H\s*(?P<sample_duration>\d*\.?\d+\s*[a-z]*)\b)*$')
_re_pattern_composition_compact_distribution = re.compile(r"[a-z]+\s*\(.+\).*\s*\+\s*([a-z]+\s*\(.+\).*\s*)+\s*$")

_re_pattern_compact_distance_strategy = re.compile(
    r'^(?P<strategy_type>[a-z_]+\b)\s*\(\s*(?P<params>-?\d*\.?\d+\s*[a-z]*\b(\s*,\s*-?\d*\.?\d+\s*[a-z]*\b)*)\s*\)\s*$')
_re_pattern_compact_leader_maneuvers = re.compile(
    r'^(?P<maneuvers_type>[a-z_]+\b)\s*\(\s*(?P<params>-?\d*\.?\d+\s*[a-z]*\b(\s*,\s*-?\d*\.?\d+\s*[a-z]*\b)*)\s*\)\s*$')
_re_pattern_compact_trace_leader_maneuvers = re.compile(
    r'^(?P<maneuvers_type>[a-z_]+\b)\s*\(\s*(?P<params>[\w/\.-]+\s*,\s*(?:False|True)\s*)\)\s*$')


def parse_unit_measurement(config_dict):
    """
    :param config_dict:
    :return update the config_dict using the international system:
    """
    for k, v in config_dict.items():
        if isinstance(v, dict):
            config_dict[k] = parse_unit_measurement(v)
        elif isinstance(v, list):
            config_dict[k] = [
                parse_and_convert_value(e) if isinstance(e, str) else parse_unit_measurement(e) for e in v]
        elif isinstance(v, str):
            config_dict[k] = parse_and_convert_value(v)
        else:
            config_dict[k] = v
    return config_dict


def parse_and_convert_value(value):
    if isinstance(value, str):
        # _re_pattern_composition_compact_distribution.match(value)
        comp_compact_dist_res, comp_err = parse_composition_compact_distribution(value)
        if comp_compact_dist_res is not None:
            return comp_compact_dist_res

        compact_dist_res, dist_err = parse_distribution_compact(value)
        if compact_dist_res is not None:
            return compact_dist_res

        return _parse_single_unit_value(value)
    return value


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


def _parse_distribution_compact_format(distribution_match):
    grp_dict = distribution_match.groupdict()
    family = grp_dict['family']
    args = [_parse_single_unit_value(value.strip()) for value in grp_dict['args'].split(',')]
    sample_duration = _parse_single_unit_value(grp_dict['sample_duration']) if grp_dict['sample_duration'] else None
    # print(f'{family} {args} {sample_duration}')
    return expand_compact_distribution_format(family, args, sample_duration)


def parse_distribution_compact(value, raise_if_error=False):
    """
    Return a tuple (<parsed value>, <exception>)
    if raise_if_error is true it raises and exception
    """
    distribution_match = _re_pattern_compact_distribution.match(value)
    if distribution_match:
        try:
            return _parse_distribution_compact_format(distribution_match), None  # match , no error
        except Exception as e:
            if raise_if_error:
                raise e
            return None, e  # match, with error
    return None, None  # no match, no error


def parse_composition_compact_distribution(value):
    composition_compact_distributions_match = _re_pattern_composition_compact_distribution.match(value)
    if composition_compact_distributions_match:
        try:
            return [parse_distribution_compact(component.strip(), raise_if_error=True)[0] for component in
                    value.split('+')], None  # match , no error
        except Exception as e:
            return None, e  # match, with error
    return None, None  # no match, no error


# def _split_and_convert_param(param_str):
#     p_name, p_value = param_str.split('=')
#     return p_name, float(_parse_single_unit_value(p_value))


class DistributionParserAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # parse the compact version of distribution
        values = parse_and_convert_value(values)
        setattr(namespace, self.dest, values)


def _expand_constant(value):
    return {'family': 'constant',
            'parameters': {'value': value}}


def _expand_uniform(min_value, max_value):
    return {'family': 'uniform',
            'parameters': {'min_value': min_value,
                           'max_value': max_value}}


def _expand_normal(mu, sigma):  # TODO min/max values <optional>
    return {'family': 'normal',
            'parameters': {'mu': mu,
                           'sigma': sigma}}


def _expand_exponential(rate, min_value=0):
    return {'family': 'exponential',
            'parameters': {'rate': rate,
                           'min_value': min_value}}


def _expand_lognormal(mu, sigma, min_value=0):
    return {'family': 'lognormal',
            'parameters': {'mu': mu,
                           'sigma': sigma,
                           'min_value': min_value}}


def _expand_erlang(k, u, min_value=0):
    return {'family': 'erlang',
            'parameters': {'k': k,
                           'u': u,
                           'min_value': min_value}}


# family : (expansion function, function arity)
_distribution_dict = {'constant': (_expand_constant, [1]),
                      'normal': (_expand_normal, [2]),
                      'uniform': (_expand_uniform, [2]),
                      'exponential': (_expand_exponential, [1, 2]),
                      'lognormal': (_expand_lognormal, [2, 3]),
                      'erlang': (_expand_erlang, [2, 3])}


class ProbabilityDistributionNotImplemented(Exception):
    pass


class ProbabilityDistributionWrongArity(Exception):
    pass


def expand_compact_distribution_format(family, args, sample_duration):
    if family not in _distribution_dict:
        raise ProbabilityDistributionNotImplemented(
            f"{family} is not implemented. Use the families {list(_distribution_dict.keys())}")

    expansion_func, num_args_options = _distribution_dict[family]
    if len(args) not in num_args_options:
        raise ProbabilityDistributionWrongArity(
            f"{family} takes  {num_args_options} argument/s, {len(args)} have provided instead.")

    expanded_distribution_config = expansion_func(*args)
    if sample_duration:
        expanded_distribution_config['sample_duration'] = sample_duration

    return expanded_distribution_config
