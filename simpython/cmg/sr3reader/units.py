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
    set_current(dimensionality, unit):
        Sets the current unit for a given dimensionality.
    get_current(dimensionality):
        Gets the current unit for a given dimensionality string.
    get_all_current():
        Returns dict with all current units.
    conversion(dimensionality, is_delta=False):
        Get unit conversion factors for a given dimensionality string.
    extract(units_table, conversion_table):
        Extracts unit information from the given tables.
    """


    def __init__(self, sr3_file, auto_read=True):
        self._unit_list = {}
        self.file = sr3_file
        if auto_read:
            self.extract()

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
        dimensionality = self._dimensionality_number(dimensionality)
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


    def _dimensionality_number(self, dimensionality):
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


    def get_current(self, dimensionality):
        """Gets the current unit for a given dimensionality string.

        Parameters
        ----------
        dimensionality : str
            Dimensionality to evaluate.
        """
        if dimensionality == "":
            return ""
        unit = ""
        if dimensionality[0] == "-":
            unit = "1"
        d = ""
        for c in dimensionality:
            if c == "|":
                unit = unit + self._unit_list[int(d)]["current"]
                d = ""
            elif c == "-":
                unit += "/"
            else:
                d = d + c
        return unit


    def get_all_current(self):
        """Returns dict with all current units.

        Parameters
        ----------
        None
        """
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


    def extract(self):
        """Extracts unit information from the sr3 file."""

        units_table = self.file.get_table("General/UnitsTable")
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

        conversion_table = self.file.get_table("General/UnitConversionTable")
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
