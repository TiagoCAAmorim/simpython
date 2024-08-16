# sr3reader/units.py
"""
units.py

This module provides functionality for handling unit conversions and management.

Classes:
--------
UnitHandler
    A class to handle unit conversions and management.

Usage Example:
--------------
unit_handler = UnitHandler(sr3_file)
unit_handler.add("m", "cm", 100, 0)
unit_handler.set_current("length", "cm")
"""

import re


class UnitHandler:
    """
    A class to handle unit conversions and management.

    Parameters
    ----------
    sr3_file : sr3reader.Sr3Handler
        SR3 file object.
    auto_read : bool, optional
        If True, reads date information from the SR3 file.
        (default: True)

    Methods
    -------
    add(old, new, gain, offset)
        Adds a new unit conversion to the unit list.
    set_current(dimensionality, unit):
        Sets the current unit for a given dimensionality.
    get_current(dimensionality):
        Gets the current unit for a given dimensionality string.
    conversion(dimensionality, is_delta=False):
        Get unit conversion factors for a given dimensionality string.
    read(units_table, conversion_table):
        Reads unit information from the given tables.
    """


    def __init__(self, sr3_file, auto_read=True):
        self._unit_list = {}
        self._file = sr3_file
        if auto_read:
            self.read()


    def add(self, old, new, gain, offset):
        """Adds a new unit in the form:
        [new unit] = [old unit] * gain + offset
        Existing units will be overwritten.

        Parameters
        ----------
        old : str
            Existing unit.
        new : str
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
        unit_numbers = self._get_unit_numbers(old)
        if len(unit_numbers) == 0:
            msg = f"{old} was not found in Master Units Table."
            raise ValueError(msg)

        for u in unit_numbers:
            g, o = self._unit_list[u]["conversion"][old]
            new_gain = g * gain
            new_offset = o * gain + offset
            self._unit_list[u]["conversion"][new] = (new_gain, new_offset)


    def set_current(self, dimensionality, unit):
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
        dimensionality = self._dimensionality2number(dimensionality)
        if unit not in self._unit_list[dimensionality]["conversion"]:
            msg = "{unit} is not a valid unit for "
            msg += f"{self._unit_list[dimensionality]['type']}."
            raise ValueError(msg)
        self._unit_list[dimensionality]["current"] = unit


    def _get_unit_numbers(self, unit):
        out = []
        for u in self._unit_list:
            for c in self._unit_list[u]["conversion"]:
                if unit == c:
                    out.append(u)
        return out


    def _dimensionality2number(self, dimensionality):
        if isinstance(dimensionality, int):
            return dimensionality
        if isinstance(dimensionality, str):
            d = [
                d
                for d in self._unit_list
                if self._unit_list[d]["type"] == dimensionality.lower()
            ]
            if len(d) == 0:
                raise ValueError(f"{dimensionality} is not a valid unit type.")
            if len(d) > 1:
                msg = f"{dimensionality} found more than once. Check code!"
                raise ValueError(msg)
            return d[0]
        msg = "Valid types for dimensionality are str and int. "
        msg += f"Got {type(dimensionality)}."
        raise TypeError(msg)


    def _transform_dimensions(self, dimensions):
        parts = dimensions.split('-')
        if len(parts) > 2:
            msg = "Invalid input format. Too many '-'s."
            raise ValueError(msg)

        def extract_integers(s):
            return [int(num) for num in re.findall(r'\d+', s)]

        numerator = extract_integers(parts[0]) if parts[0] else []
        denominator = extract_integers(parts[1]) if len(parts) > 1 else []

        return numerator, denominator


    def get_current(self, dimensionality=None):
        """Gets the current unit for a given dimensionality string.

        Parameters
        ----------
        dimensionality : str, optional
            Base dimensionality or compound dimensionality to evaluate.
            Compound dimensionality expected format:
            base dimensionalities numbers, '|' as multiplication
            and '-' as division (ex.: '1|3-2').
            If none, returns all current units.
            (default: None)
        """
        if dimensionality is None:
            return self._get_all_current()
        if dimensionality == "":
            return ""
        if dimensionality in [d["type"] for d in self._unit_list.values()]:
            d_num = self._dimensionality2number(dimensionality)
            return self._unit_list[d_num]["current"]

        numerator, denominator = self._transform_dimensions(dimensionality)
        if len(numerator) == 0:
            unit = "1"
        else:
            unit = ".".join([self._unit_list[n]["current"] for n in numerator])
        if len(denominator) > 0:
            unit += "/"
            unit += ".".join([self._unit_list[n]["current"] for n in denominator])

        return unit


    def _get_all_current(self):
        current_units = {}
        for d in self._unit_list.values():
            current_units[d["type"]] = d["current"]
        return current_units


    def conversion(self, dimensionality, is_delta=False):
        """Get unit conversion factors for a given dimensionality string.

        Parameters
        ----------
        dimensionality : str
            Dimensionality to evaluate.
        is_delat : bool, optional
            If True, the offset is ignored.
            (default: False)
        """
        if dimensionality == "":
            return (1.0, 0.0)
        gain = 1.0
        offset = 0.0
        inverse = False
        d = ""
        for c in dimensionality:
            if c == "|":
                unit = self._unit_list[int(d)]["current"]
                conversion_ = self._unit_list[int(d)]["conversion"]
                gain_new, offset_new = conversion_[unit]
                d = ""
                if inverse:
                    gain /= gain_new
                    offset = 0.0
                else:
                    gain *= gain_new
                    if is_delta:
                        offset = 0.0
                    else:
                        offset = offset * gain_new + offset_new
            elif c == "-":
                inverse = True
            else:
                d = d + c
        return (gain, offset)


    def read(self):
        """Reads unit information from the sr3 file."""

        units_table = self._file.get_table("General/UnitsTable")
        columns = zip(
            units_table["Index"],
            units_table["Dimensionality"],
            units_table["Internal Unit"],
            units_table["Output Unit"],
        )
        self._unit_list = {
            number: {
                "type": name.decode().lower(),
                "internal": internal_name.decode(),
                "current": output_name.decode(),
                "conversion": {},
            }
            for (number, name, internal_name, output_name) in columns
        }

        conversion_table = self._file.get_table("General/UnitConversionTable")
        columns = zip(
            conversion_table["Dimensionality"],
            conversion_table["Unit Name"],
            conversion_table["Gain"],
            conversion_table["Offset"],
        )
        for number, name, gain, offset in columns:
            self._unit_list[number]["conversion"][name.decode()] = (
                1.0 / gain,
                offset * (-1.0),
            )

        for d in self._unit_list.values():
            if d["internal"] != d["current"]:
                gain, offset = d["conversion"][d["internal"]]
                for k in d["conversion"]:
                    g, o = d["conversion"][k]
                    d["conversion"][k] = (g / gain, o - offset)

        for unit in self._unit_list.values():
            if unit["internal"] not in unit["conversion"]:
                unit["conversion"][unit["internal"]] = (1.0, 0.0)
