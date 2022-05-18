import sys
import yaml
import argparse

from src.utils.utils import stretch_dict, expand_dict


class ConfigurationParser:
    def __init__(self, config_file=None):
        self.config_file = config_file
        self.options = []

    def add(self, *args, **kwargs):
        self.options.append((args, kwargs))

    def parse(self, *pargs, args=None, **kwpargs):
        if args is None:
            args = sys.argv[1:].copy()

        conf_parser = argparse.ArgumentParser(add_help=False)

        config_vars = {}
        if self.config_file is not None:
            with open(self.config_file, 'r') as stream:
                config_vars = yaml.load(stream, Loader=yaml.FullLoader)
                if config_vars is None: config_vars = {}
        config_vars = stretch_dict(config_vars)
        parser = argparse.ArgumentParser(
            *pargs,
            # Inherit options from config_parser
            parents=[conf_parser],
            # Don't mess with format of description
            formatter_class=argparse.RawDescriptionHelpFormatter,
            **kwpargs,
        )

        for opt_args, opt_kwargs in self.options:

            parser_arg = parser.add_argument(*opt_args, **opt_kwargs)

            if parser_arg.dest in config_vars:
                config_default = config_vars.pop(parser_arg.dest)
                expected_type = str
                if parser_arg.type is not None:
                    expected_type = parser_arg.type

                # if not isinstance(config_default, expected_type):
                #     parser.error(f'YAML configuration entry {parser_arg.dest} does not have type {expected_type}')
                parser_arg.default = config_default
                parser_arg.required = False

        if config_vars:
            parser.error(f'Unexpected configuration entries: {config_vars}')

        res, unknown = parser.parse_known_args(args)

        return expand_dict(vars(res))
