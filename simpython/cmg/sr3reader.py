"""
Implements class Sr3Reader
"""

from datetime import datetime, timedelta
import re
from collections import OrderedDict
from pathlib import Path

import numpy as np
from scipy import interpolate # type: ignore
import h5py # type: ignore

class Sr3Reader:

    """
    Class that reads data from a sr3 file

    ...

    Attributes
    ----------
    file_path : str
        Path to sr3 file.
    wells : [str]
        List of wells found
    groups : [str]
        List of groups found
    layers : [str]
        List of layers found

    Methods
    -------
    read():
        Reads the contents of the grid file.
    write(output_file_path):
        Writes data into a grid file.
    """

    def __init__(self, file_path, include_additional_units=True):
        """
        Parameters
        ----------
        file_path : str
            Path to grid file.
        include_additional_units : bool, optional
            Defines if some additional units
            should be included.
            (default: True)
        """

        self._file_path = Path(file_path)
        if not self._file_path.is_file():
            raise FileNotFoundError(f'File not found: {self._file_path}')

        self._all_days = {}
        self._all_dates = {}
        self._unit_list = {}
        self._component_list = {}
        self._master_property_list = {}



        self.read()

        if include_additional_units:
            additional_units = [
                ('m3', 'MMm3', (1.e-6, 0.0)),
                ('bbl', 'MMbbl', (1.e-6, 0.0)),
                ('kg/cm2', 'kgf/cm2', (1., 0.0)),
            ]

            for old, new, (gain, offset) in additional_units:
                self.add_new_unit(old, new, gain, offset)
            self.set_current_unit('pressure','kgf/cm2')

    def list_hdf(self):
        """Returns dict with all groups and databases in file"""
        with h5py.File(self._file_path, 'r') as f:
            sr3_elements = {}
            def get_type(name):
                sr3_elements[name] = type(f[name])
            f.visit(get_type)
            return sr3_elements

    def read(self, read_elements=True):
        """Reads general data

        Parameters
        ----------
        read_elements : bool, optional
            Define if list of elements and properties
            should be read from sr3 file.
            (default: True)
        """
        with h5py.File(self._file_path, 'r') as f:
            self._read_master_dates(f)
            self._read_master_units(f)
            self._read_master_properties(f)

            if read_elements:
                # elements, properties, dates, days
                pass

    def _read_master_dates(self, f):
        dataset = f['General/MasterTimeTable']
        self._all_days = dict(zip(dataset['Index'], dataset['Offset in days']))

        def _parse_date(date):
            date_string = str(date)
            integer_part = int(date_string.split('.', maxsplit=1)[0]) #date_string.split('.')[0])
            decimal_part = float("0." + date_string.split('.')[1])

            parsed_date = datetime.strptime(str(integer_part), "%Y%m%d")
            fraction_of_day = timedelta(days=decimal_part)
            return parsed_date + fraction_of_day

        dataset = f['General/MasterTimeTable']
        self._all_dates = {number:_parse_date(date) for (number,date)
                           in zip(dataset['Index'], dataset['Date'])}

    def _read_master_units(self, f):
        dataset = f['General/UnitsTable']
        columns = zip(dataset['Index'],
                      dataset['Dimensionality'],
                      dataset['Internal Unit'],
                      dataset['Output Unit'])
        self._unit_list = {
            number:{
                'type':name.decode().lower(),
                'internal':internal_name.decode(),
                'current':output_name.decode(),
                'conversion':{}
                }
                  for (number,name,internal_name,output_name) in columns}

        dataset = f['General/UnitConversionTable']
        columns = zip(dataset['Dimensionality'],
                      dataset['Unit Name'],
                      dataset['Gain'],
                      dataset['Offset'])
        for (number, name, gain, offset) in columns:
            self._unit_list[number]['conversion'][name.decode()] = (1./gain, offset * (-1.))

        for d in self._unit_list.values():
            if d['internal'] != d['current']:
                gain, offset = d['conversion'][d['internal']]
                for k in d['conversion']:
                    g, o = d['conversion'][k]
                    d['conversion'][k] = (g / gain, o - offset)

        for unit in self._unit_list.values():
            if unit['internal'] not in unit['conversion']:
                unit['conversion'][unit['internal']] = (1.,0.)

    def _read_master_component_table(self, f):
        if 'ComponentTable' in f['General']:
            dataset = f['General/ComponentTable']
            self._component_list = {
                (number+1):name[0].decode() for (number,name) in enumerate(dataset[:])}
        else:
            self._component_list = {}

    def _replace_components_property_list(self, property_list):
        pattern = re.compile(r'\((\d+)\)')
        def replace(match):
            number = int(match.group(1))
            return f'({str(self._component_list.get(number, match.group(1)))})'
        return {pattern.sub(replace, k):v for k,v in property_list.items()}

    def _read_master_properties(self, f):
        dataset = f['General/NameRecordTable']
        self._master_property_list = {}
        columns = zip(dataset['Keyword'],
                      dataset['Name'],
                      dataset['Long Name'],
                      dataset['Dimensionality'])
        for (keyword,name,long_name,dimensionality) in columns:
            if keyword != '':
                keyword = keyword.decode()
                name = name.decode()
                long_name = long_name.decode()
                dimensionality = dimensionality.decode()
                if keyword[-2:] == '$C':
                    for c in self._component_list.values():
                        new_keyword = f'{keyword[:-2]}({c})'
                        self._master_property_list[new_keyword] = {
                            'name':name.replace('$C', f' ({c})'),
                            'long name':long_name.replace('$C', f' ({c})'),
                            'dimensionality_string':dimensionality}
                else:
                    self._master_property_list[keyword] = {
                        'name':name,
                        'long name':long_name,
                        'dimensionality_string':dimensionality}
        _ = self._master_property_list.pop('')

    def _unit_from_dimensionality(self, dimensionality_string):
        if dimensionality_string == '':
            return ''
        unit = ''
        if dimensionality_string[0] == '-':
            unit = '1'
        d = ''
        for c in dimensionality_string:
            if c == '|':
                unit = unit + self._unit_list[int(d)]['current']
                d = ''
            elif c == '-':
                unit = unit + '/'
            else:
                d = d + c
        return unit

    def _unit_conversion_from_dimensionality(self, dimensionality_string, is_delta=False):
        if dimensionality_string == '':
            return (1., 0.)
        gain = 1.
        offset = 0.
        inverse = False
        if dimensionality_string[0] == '-':
            inverse = True
        d = ''
        for c in dimensionality_string:
            if c == '|':
                unit = self._unit_list[int(d)]['current']
                gain_new, offset_new = self._unit_list[int(d)]['conversion'][unit]
                d = ''
                if inverse:
                    gain = gain / gain_new
                    offset = 0.
                else:
                    gain = gain * gain_new
                    if is_delta:
                        offset = 0.
                    else:
                        offset = offset * gain_new + offset_new
            elif c == '-':
                inverse = True
            else:
                d = d + c
        return (gain, offset)

    def _update_properties_units(self):
        for p in self._master_property_list.values():
            p['conversion'] = self._unit_conversion_from_dimensionality(
                p['dimensionality_string'])
            p['unit'] = self._unit_from_dimensionality(
                p['dimensionality_string'])

    def _get_unit_type_number(self, dimensionality):
        if isinstance(dimensionality, str):
            d = [d for d in self._unit_list
                 if self._unit_list[d]['type'] == dimensionality.lower()]
            if len(d) == 0:
                raise ValueError(f'{dimensionality} is not a valid unit type.')
            if len(d) > 1:
                raise ValueError(f'{dimensionality} found more than once. Check code!')
            return d[0]
        if isinstance(dimensionality, int):
            return dimensionality
        msg = f'Valid types for dimensionality are str and int. Got {type(dimensionality)}.'
        raise TypeError(msg)

    def set_current_unit(self, dimensionality, unit):
        """Sets the current unit for a given dimensionality.

        Parameters
        ----------
        dimensionality : str or int
            Dimensionality to modify.
        unit : str
            New unit for the given dimensionality.

        Raises
        ------
        ValueError
            If an invalid dimensionality is provided.
        ValueError
            If an invalid unit is provided.
        TypeError
            If an invalid dimensionality variable
            type is provided.
        """
        dimensionality = self._get_unit_type_number(dimensionality)
        if unit not in self._unit_list[dimensionality]['conversion']:
            msg = f'{unit} is not a valid unit for {self._unit_list[dimensionality]['type']}.'
            raise ValueError(msg)
        self._unit_list[dimensionality]['current'] = unit
        self._update_properties_units()

    def get_current_units(self):
        """Returns dict with current units.

        Parameters
        ----------
        None
        """
        current_units = {}
        for d in self._unit_list.values():
            current_units[d["type"]] = d["current"]

    def _get_unit_numbers(self, unit):
        out = []
        for u in self._unit_list:
            for c in self._unit_list[u]['conversion']:
                if unit == c:
                    out.append(u)
        return out

    def add_new_unit(self, old_unit, new_unit, gain, offset):
        """Adds a new unit in the form:
        [new_unit] = [old_unit] * gain + offset
        Existing units will be overwritten.

        Parameters
        ----------
        old_unit : str
            Existing unit.
        new_unit : str
            New unit.
        gain : float
            Ratio between old and new units.
        offset : float
            Offset between old and new units.

        Raises
        ------
        ValueError
            If old_unit is not found.
        """
        unit_numbers = self._get_unit_numbers(old_unit)
        if len(unit_numbers) == 0:
            raise ValueError(f'{old_unit} was not found in Master Units Table.')

        for u in unit_numbers:
            g, o = self._unit_list[u]['conversion'][old_unit]
            self._unit_list[u]['conversion'][new_unit] = (g * gain, o * gain + offset)

    def get_property_description(self, property_name):
        """Returns dict with property atributes

        Parameters
        ----------
        property_name : str
            Property to be evaluated.

        Raises
        ------
        ValueError
            If property_name is not found.
        """
        if property_name not in self._master_property_list:
            raise ValueError(f'{property_name} was not found in Master Property Table.')
        p = self._master_property_list[property_name]
        return {'description': p['name'],
                'long description': p['long name'],
                'unit': p['unit']
                }

    def get_property_unit(self, property_name):
        """Returns property current unit

        Parameters
        ----------
        property_name : str
            Property to be evaluated.

        Raises
        ------
        ValueError
            If property_name is not found.
        """
        if property_name not in self._master_property_list:
            raise ValueError(f'{property_name} was not found in Master Property Table.')
        return self._master_property_list[property_name]['unit']