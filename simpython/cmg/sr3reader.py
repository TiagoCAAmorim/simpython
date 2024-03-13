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

    def __init__(self, file_path):
        """
        Parameters
        ----------
        file_path : str
            Path to grid file.
        encoding : str, optional
            Encoding used for reading and writting files.
            (default: 'utf-8')
        auto_read : bool, optional
            Defines if should try to read input file.
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
