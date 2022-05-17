import numpy as np
import random


# import mec_platoon.config.constants as config

################################
# DISTRIBUTION FAMILY FUNCTIONS
################################
def generate_instance(func):
    def fill_parameters(*args, **kwargs):
        return lambda: func(*args, **kwargs)

    return fill_parameters


@generate_instance
def _uniform_family(min_value, max_value):
    return random.random() * (max_value - min_value) + min_value


# simpy

@generate_instance
def _discrete_uniform_family(min_value=None, max_value=None, value_step=None, values=None):
    if values is None:
        values = np.arange(min_value, max_value + value_step, value_step)
    return values[random.randint(0, len(values) - 1)]


@generate_instance
def _max_discrete_uniform_family(min_value=None, max_value=None, value_step=None, values=None):
    if values is None:
        values = np.arange(min_value, max_value + value_step, value_step)
    return values[-1]


@generate_instance
def _normal_family(mu, sigma):
    return random.gauss(mu=mu, sigma=sigma)


@generate_instance
def _constant_family(value):
    return value


@generate_instance
def _exponential_family(rate, min_value=0):
    return min_value + np.random.exponential(scale=rate)


@generate_instance
def _lognormal_family(mu, sigma, min_value=0):
    return min_value + np.random.lognormal(mean=mu, sigma=sigma) / 1000.0


@generate_instance
def _pareto(a, min_value=0):
    return min_value + np.random.pareto(a=a)


@generate_instance
def _erlang_family(k, u, min_value=0):
    # values are from [ 0, +inf) and are supposed ms -> divide by 1000 to obtain the time in seconds
    return np.random.gamma(shape=int(k), scale=u) / 1000.0 + min_value


@generate_instance
def _gamma_family(k, u, min_value=0):
    return np.random.gamma(shape=k, scale=u) / 1000.0 + min_value


@generate_instance
def _hypoexponential_family(*rates, min_value=0):
    return sum(np.random.exponential(scale=rate) for rate in rates) + min_value


delay_family_to_func = {'uniform': _uniform_family,
                        'discrete_uniform': _discrete_uniform_family,
                        'constant': _constant_family,
                        'normal': _normal_family,
                        'exponential': _exponential_family,
                        'lognormal': _lognormal_family,
                        'pareto': _pareto,
                        'erlang': _erlang_family,
                        'gamma': _gamma_family}

max_delay_family_to_func = {'discrete_uniform': _max_discrete_uniform_family,
                            'constant': _constant_family}


def get_distribution_function(family):
    return delay_family_to_func[family]


def random_from_family_distribution(family, parameters, max_value=False):
    if max_value:
        return max_delay_family_to_func[family](**parameters)
    return delay_family_to_func[family](**parameters)

#
# def random_from_config_distribution(config_key, max_value=False, default_value=None):
#     conf = config.get_config_value(config_key, error_if_missing=True, default_value=default_value)
#     family = conf[config.DELAY_DISTRIBUTION_FAMILY]
#     parameters = conf[config.DELAY_DISTRIBUTION_PARAMETERS]
#     return random_from_family_distribution(family, parameters, max_value)
