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
unit_handler = UnitHandler()
unit_handler.add("m", "cm", 100, 0)
unit_handler.set_current("length", "cm")
"""

class UnitHandler:
    """
    A class to handle unit conversions and management.

    Attributes
    ----------
    _unit_list : dict
        A dictionary to store unit conversions.

    Methods
    -------
    add(old, new, gain, offset)
        Adds a new unit conversion to the unit list.
    set_current(property_name, unit_name)
        Sets the current unit for a given property.
    """


    def __init__(self):
        self._unit_list = {}


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


    def _set_current(self, dimensionality, unit):
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
        if unit not in self._unit_list[dimensionality]["conversion"]:
            msg1 = "{unit} is not a valid unit for "
            msg2 = f"{self._unit_list[dimensionality]['type']}."
            raise ValueError(msg1+msg2)
        self._unit_list[dimensionality]["current"] = unit
        # self._update_properties_units()


    def get_current(self):
        """Returns dict with current units.

        Parameters
        ----------
        None
        """
        current_units = {}
        for d in self._unit_list.values():
            current_units[d["type"]] = d["current"]
        return current_units


    def _get_unit_numbers(self, unit):
        out = []
        for u in self._unit_list:
            for c in self._unit_list[u]["conversion"]:
                if unit == c:
                    out.append(u)
        return out


    def _get_unit_type_number(self, dimensionality):
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
        if isinstance(dimensionality, int):
            return dimensionality
        msg1 = "Valid types for dimensionality are str and int. "
        msg2 = f"Got {type(dimensionality)}."
        raise TypeError(msg1+msg2)


    def _unit_from_dimensionality(self, dimensionality_string):
        if dimensionality_string == "":
            return ""
        unit = ""
        if dimensionality_string[0] == "-":
            unit = "1"
        d = ""
        for c in dimensionality_string:
            if c == "|":
                unit = unit + self._unit_list[int(d)]["current"]
                d = ""
            elif c == "-":
                unit = unit + "/"
            else:
                d = d + c
        return unit


    def _unit_conversion_from_dimensionality(
        self, dimensionality_string, is_delta=False
    ):
        if dimensionality_string == "":
            return (1.0, 0.0)
        gain = 1.0
        offset = 0.0
        inverse = False
        if dimensionality_string[0] == "-":
            inverse = True
        d = ""
        for c in dimensionality_string:
            if c == "|":
                unit = self._unit_list[int(d)]["current"]
                conversion_ = self._unit_list[int(d)]["conversion"]
                gain_new, offset_new = conversion_[unit]
                d = ""
                if inverse:
                    gain = gain / gain_new
                    offset = 0.0
                else:
                    gain = gain * gain_new
                    if is_delta:
                        offset = 0.0
                    else:
                        offset = offset * gain_new + offset_new
            elif c == "-":
                inverse = True
            else:
                d = d + c
        return (gain, offset)


    # @_need_read_file  # type: ignore-arg-type]
    def _read_master_units(self, units_table, conversion_table):
        # units_table = self._f["General/UnitsTable"]
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

        # conversion_table = self._f["General/UnitConversionTable"]
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
