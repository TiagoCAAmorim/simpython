"""
Implements the class TemplateProcessor
"""
from pathlib import Path
import re
from pyDOE import lhs  # type: ignore
from scipy import stats  # type: ignore

import numpy as np  # type: ignore # noqa: F401
import pandas as pd  # type: ignore # noqa: F401


class TemplateProcessor:

    """
    Class that represents a project to generate files based on a template

    ...

    Attributes
    ----------
    variables_raw : list
        List of all variable-type definition found
        in template file.
    variables : dict
        dictionary with all data related to the
        variables: distribution, parameters, values
        (if Table type), default value, if is active.
    experiments_table : data-frame
        Table with all experiments.

    Methods
    -------
    list_valid_distributions()
        Lists all valid distribution and respective arguments.
    set_output_file(output_file_path)
        Sets the output file path.
    set_encoding(encoding)
        Sets the encoding used for reading and writing files.
    set_n_samples(n_samples)
        Sets the number of samples to be generated.
    read_variables_table(variables_table_path)
        Reads csv file with values for the Table variables.
    set_variable_active(variable, active=True):
        Sets a variable to active/inactive.
    generate_experiments(n_samples=0, all_uniform=None):
        Generates a table (experiments_table) with all experiments.
    create_new_files(output_file_path=None):
        Creates files based on samples.
    """

    def __init__(self, template_path, verbose=False, output_file_path=None,
                 variables_table_path=None, all_uniform=False, n_samples=0,
                 encoding='utf-8'):
        """
        Parameters
        ----------
        template_path : str
            Path to template file.
        verbose : boolean, optional
            Indicates if additional messages should be print.
            (default: False)
        output_file_path : str, optional
            Path to the files to be written.
            (default: None)
        variables_table_path : str, optional
            Path to csv file to be read with values of the
            Table type variables.
            (default: None)
        all_uniform : boolean, optional
            Indicates if distributions should be ignored and a
            uniform be applied to all variables.
            (default: False)
        n_samples : int, optional
            Number of samples to be generated.
            (default: 0)
        encoding : str, optional
            Encoding used for reading and writing files.
            (default: 'utf-8')
        """

        self._template_path = Path(template_path)
        if not self._template_path.exists():
            raise FileNotFoundError(
                f"Template file '{self._template_path}' not found.")

        self._verbose = verbose
        self._all_uniform = all_uniform
        self._encoding = encoding

        self._valid_distributions = {
            'uniform':      {'parameters': 2,
                             'description': ('minimum', 'maximum'),
                             'types': ['int', 'float']},
            'normal':       {'parameters': 2,
                             'description': ('mean', 'std_var'),
                             'types': ['float']},
            'truncnormal':  {'parameters': 4,
                             'description': ('mean', 'std_var', 'minimum', 'maximum'),
                             'types': ['float']},
            'lognormal':    {'parameters': 2,
                             'description': ('mean', 'std_var'),
                             'types': ['float']},
            'triangular':   {'parameters': 3,
                             'description': ('minimum', 'maximum', 'most_likely'),
                             'types': ['float']},
            'constant':     {'parameters': 1,
                             'description': ('value',),
                             'types': ['int', 'float', 'str']},
            'categorical':  {'parameters': 2,
                             'description': ('values_list', 'probabilities_list'),
                             'types': ['int', 'float', 'str']},
            'table':        {'parameters': 0,
                             'description': ('no parameters',),
                             'types': ['str']}
        }
        # std_dev from mean to define limits of normal distribution variables when
        # using option all_uniform=True
        self._normal_limits_as_uniform = 2.

        self.variables_raw = self._extract_raw_text()
        self.variables = self._parse_variables()

        if variables_table_path is not None:
            self.read_variables_table(variables_table_path)

        self.experiments_table = None
        self._current_distribution = None
        self._n_samples = n_samples
        if output_file_path is not None:
            self.set_output_file(output_file_path)
            self.generate_experiments(n_samples=self._n_samples)
            self.create_new_files()

    def __str__(self):
        return str(self.variables)

    def list_valid_distributions(self):
        """Lists all valid distribution and respective arguments."""

        for k, v in self._valid_distributions.items():
            msg1 = f"{k} distribution - parameters: {', '.join(v['description'])};"
            msg2 = f"valid type(s): {', '.join(v['types'])}"
            print(" ".join([msg1, msg2]))

    def _extract_contents(self, text, start=r'\(', end=r'\)'):
        pattern = f'{start}(.*?){end}'
        matches = re.findall(pattern, text)
        return matches

    def _custom_split(self, text, sep=',', start='{', end='}'):
        result = []
        current_token = ''
        paren_count = 0

        for char in text:
            if char == sep and paren_count == 0:
                result.append(current_token.strip())
                current_token = ''
            elif char == start:
                paren_count += 1
                current_token += char
            elif char == end:
                paren_count -= 1
                current_token += char
            else:
                current_token += char

        result.append(current_token.strip())
        return result

    def _extract_raw_text(self):
        variables_raw = []
        with open(self._template_path, 'r', encoding=self._encoding) as file:
            for line_num, line in enumerate(file, start=1):
                if line.count(r'<\var>') != line.count('<var>'):
                    raise ValueError(
                        f"Unclosed <\\var> <var> at line {line_num}.")
                parts = self._extract_contents(
                    text=line, start=r'<\\var>', end=r'<var>')
                if len(parts) > 0:
                    for part in parts:
                        var = part.strip()
                        if var == '':
                            raise ValueError(
                                f"Empty variable name at line {line_num}.")
                        variables_raw.append(var)
        return variables_raw

    def _transform_variable(self, variable, variable_type):
        if isinstance(variable, list):
            var = []
            for v in variable:
                var.append(self._transform_variable(
                    variable=v, variable_type=variable_type))
                if var[-1] is None:
                    return None
            return var
        try:
            var_type = {'int': int,
                        'str': str,
                        'float': float}[variable_type.strip().lower()]
            return var_type(variable)
        except (ValueError, TypeError, NameError):
            return None

    def _parse_distribution(self, text, var_type):
        if text is None:
            if self._verbose:
                print("  No distribution provided. Will assume 'table'.")
            return 'table', list()

        parameters = self._custom_split(text)
        distribution = parameters[0].lower()
        if distribution not in self._valid_distributions:
            raise ValueError(f"Invalid distribution: '{distribution}'.")
        parameters = parameters[1:]
        if len(parameters) != self._valid_distributions[distribution]['parameters']:
            expected = self._valid_distributions[distribution]['parameters']
            msg1 = f"Invalid number of parameters for distribution '{distribution}'."
            msg2 = f" Expected {expected}, found {len(parameters)}."
            raise ValueError(" ".join([msg1, msg2]))

        if var_type is not None:
            if var_type not in self._valid_distributions[distribution]['types']:
                types = ', '.join(
                    self._valid_distributions[distribution]['types'])
                msg1 = f"Invalid type ({var_type})"
                msg2 = f"for distribution '{distribution}'."
                msg3 = f"Valid option(s): {types}."
                raise ValueError(" ".join([msg1, msg2, msg3]))

            if distribution == 'categorical':
                param_list = parameters[0].lstrip('{').rstrip('}').split(',')
            else:
                param_list = parameters

            for i, p in enumerate(param_list):
                new_value = self._transform_variable(
                    variable=p, variable_type=var_type)
                if new_value is None:
                    msg1 = f"Parameters for distribution '{distribution}'"
                    msg2 = f"must be of type {var_type}."
                    msg3 = f"Cannot transform '{param_list[i]}'."
                    raise ValueError(" ".join([msg1, msg2, msg3]))
                param_list[i] = new_value

            if distribution == 'categorical':
                parameters[0] = param_list
            else:
                parameters = param_list

        if distribution == 'categorical':
            param_list = parameters[1].lstrip('{').rstrip('}').split(',')
            if len(parameters[0]) != len(param_list):
                msg1 = f"Inconsistent number of values in distribution '{distribution}'."
                msg2 = f"Values found: {len(parameters[0])},"
                msg3 = f"associated probabilities: {len(param_list)}."
                raise ValueError(" ".join([msg1, msg2, msg3]))
            for i, p in enumerate(param_list):
                new_value = self._transform_variable(
                    variable=p, variable_type='float')
                if new_value is None:
                    msg1 = f"Probabilities for distribution '{distribution}'"
                    msg2 = f"must be of type float. Cannot transform '{p}'."
                    raise ValueError(" ".join([msg1, msg2]))
                param_list[i] = new_value
            s = sum(param_list)
            cum_list = [sum(param_list[:i+1]) /
                        s for i in range(len(param_list))]
            parameters[1] = cum_list

        return distribution, parameters

    def _check_variable_type(self, default, distribution, parameters):
        var_type = None
        for test_type in self._valid_distributions[distribution]['types']:
            if var_type is None:
                var_type = test_type

                if default is not None:
                    default_mod = self._transform_variable(variable=default,
                                                           variable_type=test_type)
                    if default_mod is None:
                        var_type = None
                    else:
                        default = default_mod

                param_out = []
                for param in parameters:
                    if var_type is not None:
                        param_out.append(self._transform_variable(variable=param,
                                                                  variable_type=var_type))
                        if param_out[-1] is None:
                            var_type = None

                if var_type is not None:
                    parameters = param_out

                    if self._verbose:
                        print(f"  No type provided. Will assume '{var_type}'.")

        return default, distribution, parameters, var_type

    def _parse_variable_options(self, text):
        default = None
        var_type = None

        distribution_text = self._extract_contents(
            text=text, start=r'\(', end=r'\)')
        if len(distribution_text) > 1:
            msg1 = f"Bad distribution options format in: '{text}'."
            msg2 = "Only one distribution with ( and ) can be defined."
            raise ValueError(" ".join([msg1, msg2]))

        options = self._custom_split(text=text, start='(', end=')')
        if len(distribution_text) == 1:
            if '(' not in options[-1] or ')' not in options[-1]:
                msg1 = "Distribution options with ( and ) must be"
                msg2 = f"the last information in: '{options}'."
                raise ValueError(" ".join([msg1, msg2]))
            options = options[:-1]
            distribution_text = distribution_text[0].strip()
        else:
            distribution_text = None

        if len(options) > 2:
            msg1 = f"Bad options format in: '{options}'."
            msg2 = " Too many options."
            raise ValueError(" ".join([msg1, msg2]))
        if len(options) > 0:
            if len(options) > 1 or options[0] != '':
                default = options[-1].strip()
                if len(options) == 2:
                    var_type = options[0].strip()
                    default = self._transform_variable(
                        variable=default, variable_type=var_type)
                    if default is None:
                        msg1 = f"Default value ({options[-1]})"
                        msg2 = "must be of the defined type ({var_type})."
                        raise ValueError(" ".join([msg1, msg2]))

        distribution, parameters = self._parse_distribution(
            distribution_text, var_type)

        if var_type is None:
            check_type = self._check_variable_type(
                default, distribution, parameters)
            default, distribution, parameters, var_type = check_type
        if var_type is None:
            msg1 = "Couldn't find the variable type based on provided data: "
            msg2 = f"'{text}'. Possible type(s) for {distribution} are:"
            msg3 = f"{', '.join(self._valid_distributions[distribution]['types'])}."
            raise ValueError(" ".join([msg1, msg2, msg3]))

        return {'active': True,
                'distribution': distribution,
                'parameters': parameters,
                'default': default,
                'type': var_type}

    def _parse_key(self, text):
        key = text.split('[')[0].strip()
        if len(key) == 0:
            raise ValueError(f"Undefined variable name in: '{text}'.")
        return key

    def _parse_options(self, text):
        options = self._extract_contents(text=text, start=r'\[', end=r'\]')
        if len(options) > 1:
            msg1 = f"Bad options format in: '{text}'."
            msg2 = "Only one list with [ and ] can be defined."
            raise ValueError(" ".join([msg1, msg2]))

        if len(options) == 1:
            options_dict = self._parse_variable_options(options[0])
        else:
            options_dict = self._parse_variable_options('')

        return options_dict

    def _parse_variables(self):
        # General pattern: Variable[type, default, (distribution, par1, par2)]
        variables = {}
        repetition = []
        for text in self.variables_raw:
            if self._verbose:
                print(f'Command found: {text}')
            key = self._parse_key(text)
            if key in variables:
                if self._verbose and key not in repetition:
                    print(
                        f'  key {key} found more than once. Ignoring options in repetitions.')
                    repetition.append(key)
            else:
                options = self._parse_options(text)
                variables[key] = options
                if self._verbose:
                    print(f'  key: {key}')
                    print(f'  options: {options}')
        return variables

    def set_output_file(self, output_file_path):
        """Sets the output file path.

        Parameters
        ----------
        output_file_path : str
            Path to the files to be written.

        Raises
        ------
        ValueError
            If an invalid path is provided.
        """

        if output_file_path is None:
            self._output_file_path = None
        else:
            try:
                self._output_file_path = Path(output_file_path)
            except (ValueError, TypeError, NameError) as exc:
                self._output_file_path = None
                msg = f'Invalid file path: {str(output_file_path)}'
                raise ValueError(msg) from exc

    def set_encoding(self, encoding):
        """Sets the encoding used for reading and writing files.

        Parameters
        ----------
        encoding : str
            Encoding used for reading and writing files.

        """
        self._encoding = encoding

    def set_n_samples(self, n_samples):
        """Sets the number of samples to be generated.

        Parameters
        ----------
        n_samples : int
            Number of samples.

        """
        self._n_samples = n_samples

    def read_variables_table(self, variables_table_path):
        """Reads csv file with values for the Table variables.

        Parameters
        ----------
        variables_table_path : str
            Path to csv file to be read with values of the
            Table type variables.

        Raises
        ------
        ValueError
            If an error is found when reading file.
        """

        if not Path(variables_table_path).exists():
            print(f"CSV file '{variables_table_path}' not found.")
        else:
            try:
                df = pd.read_csv(variables_table_path, skipinitialspace=True)
                for key in df.columns:
                    if key not in self.variables:
                        msg1 = f"Variable '{key}' not found in template."
                        msg2 = "Will ignore data."
                        print(" ".join([msg1,msg2]))
                        continue
                    if self.variables[key]['distribution'] != 'table':
                        msg1 = f"Variable '{key}' already has a distribution."
                        msg2 = "Will ignore data."
                        print(" ".join([msg1,msg2]))
                        continue
                    self.variables[key]['values'] = list(df[key])
            except (ValueError, TypeError, NameError) as e:
                msg = 'Error reading variables table file:'
                raise ValueError(" ".join([msg, variables_table_path])) from e

    def _check_generate_experiments(self, n_samples=0):
        tables_n_values = []
        for data in self.variables.values():
            if data.get('distribution', False) == 'table':
                tables_n_values.append(len(data.get('values', [])))

        if len(tables_n_values) > 0:
            if not min(tables_n_values) == max(tables_n_values):
                msg1 = "Number of entries in 'table' variables is inconsistent,"
                msg2 = f"ranging from {min(tables_n_values)}"
                msg3 = f"to {max(tables_n_values)}."
                msg4 = "Cannot continue."
                print(" ".join([msg1, msg2, msg3, msg4]))
                return None
            tables_n_values = tables_n_values[0]
            if tables_n_values == 0:
                print("No values found for 'table' variables. Cannot continue.")
                return None
        else:
            tables_n_values = n_samples

        if n_samples < 1 and tables_n_values > 0:
            n_samples = tables_n_values
        elif n_samples < 1:
            msg1 = f"Requested sample size ({n_samples})"
            msg2 = "is smaller than minimum (1)."
            msg3 = "Cannot continue."
            print(" ".join([msg1, msg2, msg3]))
            return None
        elif tables_n_values != n_samples:
            msg1 = f"Number of values in 'table' variables ({tables_n_values})"
            msg2 = "is different from the requested sample size"
            msg3 = f"({n_samples})."
            msg4 = "Cannot continue."
            print(" ".join([msg1, msg2, msg3, msg4]))
            return None

        return n_samples

    def _inv_cdf(self, probability, data, all_uniform):
        if min(probability) < 0:
            raise ValueError("Probability lower than zero!")
        if max(probability) > 1:
            raise ValueError("Probability larger than one!")

        distribution = data['distribution']
        parameters = data['parameters']

        if distribution == 'constant':
            return parameters[0]

        if distribution == 'categorical':
            if all_uniform:
                n = len(parameters[0])
                p_cum_list = [(i+1) / n for i in range(n)]
            else:
                p_cum_list = parameters[1]

            def cat_prob(x):
                for i, p in enumerate(p_cum_list):
                    if p >= x:
                        return parameters[0][i]
                raise ValueError("Error in categorical probabilities!")
            vec_cat_prob = np.vectorize(cat_prob)
            return vec_cat_prob(probability)

        if distribution == 'uniform' or (distribution == 'triangular' and all_uniform):
            loc = parameters[0]
            scale = parameters[1] - parameters[0]
            if isinstance(loc, int) and isinstance(scale, int):
                return np.int32(stats.randint.ppf(probability, low=loc, high=loc+scale+1))
            return stats.uniform.ppf(probability, loc=loc, scale=scale)

        if distribution == 'triangular':
            loc = parameters[0]
            scale = parameters[1] - parameters[0]
            c = (parameters[2] - parameters[0]) / scale
            return stats.triang.ppf(probability, c, loc=loc, scale=scale)

        if distribution == 'normal':
            mean = parameters[0]
            std_dev = parameters[1]
            if all_uniform:
                loc = mean - std_dev * self._normal_limits_as_uniform
                scale = 2 * std_dev * self._normal_limits_as_uniform
                return stats.uniform.ppf(probability, loc=loc, scale=scale)
            return stats.norm.ppf(probability, loc=mean, scale=std_dev)

        if distribution == 'truncnormal':
            mean = parameters[0]
            std_dev = parameters[1]
            a = parameters[2]
            b = parameters[3]
            if all_uniform:
                return stats.uniform.ppf(probability, loc=a, scale=b-a)
            lower_limit = (a - mean) / std_dev
            upper_limit = (b - mean) / std_dev
            return stats.truncnorm.ppf(probability,
                                       lower_limit, upper_limit,
                                       loc=mean, scale=std_dev)

        if distribution == 'lognormal':
            mean = parameters[0]
            std_dev = parameters[1]
            if all_uniform:
                loc = mean - std_dev * self._normal_limits_as_uniform
                scale = 2 * std_dev * self._normal_limits_as_uniform
                return stats.uniform.ppf(probability, loc=loc, scale=scale)
            return stats.lognorm.ppf(probability, s=std_dev, scale=np.exp(mean))

        raise ValueError(f"Unknown distribution: {distribution}.")

    def set_variable_active(self, variable, active=True):
        """Sets a variable to active/inactive.

        Parameters
        ----------
        variable : str
            Variable name.
        active : boolean, optional
            Define if the variable is active.
            (default: True)

        Raises
        ------
        ValueError
            If an invalid variable is provided.
        ValueError
            If variable is set to inactive, but does not have
            a default value.
        """

        if variable not in self.variables:
            raise ValueError(f"Unknown variable: {variable}.")
        if not active and self.variables[variable]['default'] is None:
            raise ValueError(
                f"Cannot deactivate a variable without a default value: {variable}.")
        self.variables[variable]['default'] = active

    def generate_experiments(self, n_samples=0, all_uniform=None):
        """Generates a table (experiments_table) with all experiments.

        Parameters
        ----------
        n_samples : int, optional
            Number of samples to be generated.
            (default: 0)
        all_uniform : boolean, optional
            Indicates if distributions should be ignored and a
            uniform be applied to all variables.
            (default: False)
        """

        if self._verbose:
            print('Checking parameters')
        n_samples = self._check_generate_experiments(n_samples=n_samples)
        if n_samples < 1:
            self.experiments_table = None
            return

        if all_uniform is None:
            all_uniform = self._all_uniform

        if self._verbose:
            print('Building experiments')

        if len(self.variables) == 1:
            iterations = 1
        else:
            iterations = min(100, max(1, int(1e6*np.power(n_samples, -2.))))
        samples = lhs(len(self.variables),
                      samples=n_samples,
                      criterion='maximin',
                      iterations=iterations)

        if self._verbose:
            print('Calculating inverse CDF')
        df = pd.DataFrame()
        for column_index, var in enumerate(self.variables):
            data = self.variables[var]
            if self._verbose:
                print(f"   {var}: {data['distribution']}")
            if not data['active']:
                df[var] = [data['default']] * n_samples
            elif data['distribution'] == 'table':
                df[var] = data['values']
            else:
                df[var] = self._inv_cdf(
                    samples[:, column_index], data, all_uniform)
        self.experiments_table = df

    def _create_new_file(self, output_file_path, values, text):
        new_text = text
        for var, data in self.variables.items():
            pattern = f'<\\\\var>{var}[^<]+<var>'
            value = self._transform_variable(values[var], data['type'])
            new_text = re.sub(pattern, str(value), new_text)
        with open(output_file_path, 'w', encoding=self._encoding) as f:
            f.write(new_text)

    def create_new_files(self, output_file_path=None):
        """Creates files based on samples.

        Parameters
        ----------
        output_file_path : str, optional
            Path to the files to be written. Uses value stored
            in output_file_path if None is provided.
            (default: None)
        """

        if output_file_path is not None:
            self.set_output_file(output_file_path)
        if self._output_file_path is None:
            print('Output file not defined. Cannot continue.')
            return
        if self.experiments_table is None:
            self.generate_experiments()
            if self.experiments_table is None:
                print('Experiments table could not be created. Cannot continue.')
                return

        with open(self._template_path, 'r', encoding=self._encoding) as f:
            text = f.read()

        self._output_file_path.parent.mkdir(parents=True, exist_ok=True)
        for index, row in self.experiments_table.iterrows():
            file_path_ = self._output_file_path.stem
            file_suffix_ = self._output_file_path.suffix
            file_name = f"{file_path_}_{index}{file_suffix_}"
            new_file_path = self._output_file_path.with_name(file_name)
            self._create_new_file(new_file_path, row.to_dict(), text)
