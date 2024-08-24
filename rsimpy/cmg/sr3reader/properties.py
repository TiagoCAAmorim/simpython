# sr3reader/properties.py
"""
properties.py

This module provides functionality for handling properties.

Classes:
--------
PropertyHandler
    A class to handle properties.

Usage Example:
--------------
property_handler = PropertyHandler(sr3_file, units_handler, grid_handler)
qo_str = property_handler.unit("OILRATSC")
gain, offset = property_handler.conversion("OILRATSC")
"""

import re
from rsimpy.common import utils
from .elements import ElementHandler


class PropertyHandler:
    """
    A class to handle properties.

    Parameters
    ----------
    sr3_file : sr3reader.Sr3Handler
        SR3 file object.
    units : sr3reader.UnitsHandler
        Units handler object.
    grid : sr3reader.GridHandler
        Grid handler object.
    auto_read : bool, optional
        If True, reads date information from the SR3 file.
        (default: True)

    Methods
    -------
    read(self)
        Reads property information from the sr3 file.
    get(self, element=None, name=None)
        Gets property or property list.
    get_components_list(self)
        Returns a list of components.
    description(self, property_name)
        Returns a dictionary with property attributes.
    dimensionality(self, property_name)
        Returns the dimensionality of a property.
    unit(self, property_name)
        Returns the current unit of a property.
    conversion(self, property_name)
        Returns the unit conversion of a property.
    set_alias(self, old, new, return_error=True)
        Sets an alias for an existing property.
    """


    def __init__(self, sr3_file, units, grid, auto_read=True):
        self._properties = {}
        self._component_list = {}
        self._element_properties = {k:{} for k in ElementHandler.valid_elements()}
        self._file = sr3_file
        self._units = units
        self._grid = grid

        if auto_read:
            self.read()


    def read(self):
        """Reads property information from the sr3 file."""
        property_table = self._file.get_table("General/NameRecordTable")
        components_table = self._file.get_table("General/ComponentTable")

        if components_table is not None:
            self._extract_components_table(components_table)
        self._extract_property_table(property_table)

        for k in ElementHandler.valid_elements():
            self._element_properties[k] = self._extract_element_properties(k)


    def _extract_property_table(self, dataset):
        self._properties = {}
        columns = zip(
            dataset["Keyword"],
            dataset["Name"],
            dataset["Long Name"],
            dataset["Dimensionality"],
        )
        for keyword, name, long_name, dimensionality in columns:
            if keyword != "":
                keyword = keyword.decode()
                name = name.decode()
                long_name = long_name.decode()
                dimensionality = dimensionality.decode()
                if keyword[-2:] == "$C":
                    for c in self._component_list.values():
                        new_keyword = f"{keyword[:-2]}({c})"
                        self._properties[new_keyword] = {
                            "name": name.replace("$C", f" ({c})"),
                            "long name": long_name.replace("$C", f" ({c})"),
                            "dimensionality": dimensionality,
                        }
                else:
                    self._properties[keyword] = {
                        "name": name,
                        "long name": long_name,
                        "dimensionality": dimensionality,
                    }
        _ = self._properties.pop("")


    def _extract_components_table(self, dataset, ignore_water=False):
        self._component_list = {
            (number + 1): name[0].decode()
            for (number, name) in enumerate(dataset[:])
            if not (name[0].decode() == "WATER" and ignore_water)
        }


    def _extract_element_properties(self, element_type):
        if element_type == "grid":
            properties = self._grid.get_property()
        else:
            data = self._file.get_element_table(
                element_type=element_type,
                dataset_string="Variables"
            )
            properties = {
                name.decode(): number
                for (number, name) in enumerate(data[:])
            }
        return self._replace_components(properties)


    def get(self, element_type=None, name=None, throw_error=True):
        """Get property number or property dict.

        Parameters
        ----------
        element : str, optional
            Element type.
            Returns master properties table if None.
            (default : None)
        name : str or [str], optional
            Property name.
            Returns all element properties if None.
            (default : None)

        Raises
        ------
        ValueError
            If element type is not defined and a property name is provided.
        ValueError
            If property name is not found.
        """
        if element_type is None:
            if name is not None:
                msg = "Element type must be defined if a property name is provided."
                raise ValueError(msg)
            return self._properties
        ElementHandler.is_valid(element_type, throw_error=True)
        if name is None:
            return self._element_properties[element_type]

        if utils.is_vector(name):
            return {k: self.get(element_type, k, throw_error) for k in name}

        if name in self._element_properties[element_type]:
            return self._element_properties[element_type][name]
        if throw_error:
            msg = f"Property {name} not found for '{element_type}'."
            raise ValueError(msg)
        return None


    def get_components_list(self):
        """Returns list of components."""
        return self._component_list


    def _replace_components(self, property_list):
        """Returns list or dict that replaces components numbers to names.

        Parameters
        ----------
        property_list : [str] or dict
            Property list or dictionary.
        """
        pattern = re.compile(r"\((\d+)\)")

        def _replace(match):
            number = int(match.group(1))
            return f'({str(self._component_list.get(number, match.group(1)))})'
        if isinstance(property_list, dict):
            return {pattern.sub(_replace, k): v
                    for k, v in property_list.items()}
        return [pattern.sub(_replace, k) for k in property_list]


    def description(self, property_name):
        """Returns dict with property attributes.

        Parameters
        ----------
        property_name : str
            Property to be evaluated.

        Raises
        ------
        ValueError
            If property_name is not found.
        """
        if property_name not in self._properties:
            msg = f"{property_name} was not found in Master Property Table."
            raise ValueError(msg)
        p = self._properties[property_name]
        return {
            "description": p["name"],
            "long description": p["long name"],
            "unit": self._units.get_current(p["dimensionality"]),
        }


    def dimensionality(self, property_name):
        """Returns property dimensionality.

        Parameters
        ----------
        property_name : str
            Property to be evaluated.

        Raises
        ------
        ValueError
            If property_name is not found.
        """
        if property_name not in self._properties:
            msg = f"{property_name} was not found in Master Property Table."
            raise ValueError(msg)
        d = self._properties[property_name]["dimensionality"]
        return d


    def unit(self, property_name):
        """Returns property current unit.

        Parameters
        ----------
        property_name : str
            Property to be evaluated.

        Raises
        ------
        ValueError
            If property_name is not found.
        """
        d = self.dimensionality(property_name)
        return self._units.get_current(d)


    def conversion(self, property_name):
        """Returns property current unit conversion.

        Parameters
        ----------
        property_name : str
            Property to be evaluated.

        Raises
        ------
        ValueError
            If property_name is not found.
        """
        d = self.dimensionality(property_name)
        return self._units.conversion(d)


    def set_alias(self, old, new, return_error=True):
        """Sets an alias for an existing property.

        Parameters
        ----------
        old : str
            Original property.
        new : str
            New property alias.
        check_error : bool, optional
            Raises error if problems are found.
            (default : True)

        Raises
        ------
        ValueError
            If old property does not exist.
        ValueError
            If new property already exists.
        """
        if old not in self._properties:
            msg = f'Property not found: {old}'
            raise ValueError(msg)
        if new in self._properties and return_error:
            msg = f'Property already exists: {new}'
            raise ValueError(msg)

        self._properties[new] = self._properties[old]

        for k in self._element_properties:
            if old in self._element_properties[k]:
                p = self._element_properties[k][old]
                self._element_properties[k][new] = p
