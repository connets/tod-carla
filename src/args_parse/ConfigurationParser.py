import sys
import yaml
import argparse
import re
from src.utils.utils import stretch_dict, expand_dict


class ConfigurationParser:
    """
    A class used to parse the args with configuration files
    """

    def __init__(self, config_file=None):
        """
        Parameters
        ----------
        config_file : str
            take the path of the file with default configurations
               """
        self.config_file = config_file
        self.options = []

    def add(self, *args, **kwargs):
        """
        add name arguments and option for that arguments
        """
        self.options.append((args, kwargs))

    # TODO we can remove pargs?
    def parse(self, *pargs, args=None, **kwpargs):
        """
        run the parsing of the current state of the object.
        Parameters
        ----------
            pargs: parsing options
            args: arguments to parse, if None take command line arguments


        """
        if args is None:
            args = sys.argv[1:].copy()

        conf_parser = argparse.ArgumentParser(add_help=False)

        config_vars_complete = {}
        if self.config_file is not None:
            with open(self.config_file, 'r') as stream:
                config_vars_complete = yaml.load(stream, Loader=yaml.FullLoader)
                if config_vars_complete is None: config_vars_complete = {}
        config_vars_complete = stretch_dict(config_vars_complete)

        if 'IMPORT.$cmd$' in config_vars_complete.keys():
            for imp in config_vars_complete['IMPORT.$cmd$'].strip().split(';'):
                exec(imp)

            del config_vars_complete['IMPORT.$cmd$']

        config_vars = {}
        config_keys_to_exec = []
        for key in config_vars_complete.keys():
            m = re.search(r'(.*)\.\$cmd\$$', key)
            if m:
                code = config_vars_complete[key]
                config_vars[m.group(1)] = code
                config_keys_to_exec.append(m.group(1))
            else:
                config_vars[key] = config_vars_complete[key]

        config_private_vars = {key: config_vars[key] for key in config_vars.keys() if key.startswith('_')}
        config_vars = {key: config_vars[key] for key in config_vars.keys() if not key.startswith('_')}

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
                parser_arg.default = config_default
                parser_arg.required = False

        if config_vars:
            parser.error(f'Unexpected configuration entries: {config_vars}')

        res, unknown = parser.parse_known_args(args)
        res = vars(res)

        res = {**res, **config_private_vars}
        for key in config_keys_to_exec:
            print(key)
            code = res[key]
            code = code.replace('self', 'res')
            res[key] = eval(code)

        res = {key: res[key] for key in res.keys() if not key.startswith('_')}

        return expand_dict(res)
