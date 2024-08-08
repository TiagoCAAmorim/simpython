"""
Implements class Sr3Reader
"""

from datetime import datetime, timedelta
import re
from collections import OrderedDict
from pathlib import Path

import numpy as np
from scipy import interpolate  # type: ignore
import h5py  # type: ignore


def _need_read_file(func):  # pylint: disable=no-self-argument
    def wrapper(self, *args, **kwargs):
        self.open()
        result = func(self, *args, **kwargs)  # pylint: disable=not-callable
        self.close()
        return result

    return wrapper


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
    sector : [str]
        List of sectors found
    layers : [str]
        List of layers found

    Methods
    -------
    read():
        Reads the contents of the grid file.
    write(output_file_path):
        Writes data into a grid file.
    get_elements(element_type):
        Returns a list of the elements
        associated to the element type.
    get_properties(element_type):
        Returns a list of the properties
        associated to the element type.
    """

    def __init__(self, file_path, usual_units=True):
        """
        Parameters
        ----------
        file_path : str
            Path to grid file.
        usual_units : bool, optional
            Adds some extra units
            and changes current units.
            (default: True)
        """

        self._file_path = Path(file_path)
        if not self._file_path.is_file():
            raise FileNotFoundError(f"File not found: {self._file_path}")

        self._f = None
        self._open_count = 0
        self._open_calls = 0
        self._group_type = None
        self._dataset_type = None

        self._all_days = {}
        self._all_dates = {}
        self._unit_list = {}
        self._component_list = {}
        self._master_property_list = {}

        self._element_types = [
            "well",
            "group",
            "sector",
            "layer",
            "special",
            "grid"
        ]
        self._element = {"special": {"": 0}, "grid": {"MATRIX": 0}}
        self._parent = {}
        self._connection = {}
        self._property = {}
        self._timestep = {}
        self._day = {}
        self._date = {}

        self._grid_size = {}

        self.read()

        if usual_units:
            additional_units = [
                ("m3", "MMm3", (1.0e-6, 0.0)),
                ("bbl", "MMbbl", (1.0e-6, 0.0)),
                ("kg/cm2", "kgf/cm2", (1.0, 0.0)),
            ]

            for old, new, (gain, offset) in additional_units:
                self.add_new_unit(old, new, gain, offset)
            self.set_current_unit("pressure", "kgf/cm2")

    def _file_is_closed(self):
        return self._f is None

    def _file_is_open(self):
        return not self._file_is_closed()

    def open(self):
        """Manually open sr3 file."""
        if self._file_is_closed():
            self._f = h5py.File(self._file_path)
            self._open_calls += 1
            self._open_count = 0
        self._open_count += 1

    def close(self, force_close=False):
        """Manually close sr3 file."""
        if self._file_is_closed():
            self._open_count = 0
        else:
            if force_close:
                self._open_count = 1
            if self._open_count == 1:
                self._f.close()
                self._f = None
            self._open_count -= 1

    @_need_read_file  # type: ignore[arg-type]
    def get_hdf_elements(self):
        """Returns dict with all groups and databases in file"""
        sr3_elements = []

        def get_type(name):
            sr3_elements.append((name, type(self._f[name])))

        self._f.visit(get_type)
        return sr3_elements

    @_need_read_file  # type: ignore[arg-type]
    def read(self, read_elements=True):
        """Reads general data

        Parameters
        ----------
        read_elements : bool, optional
            Define if list of elements and properties
            should be read from sr3 file.
            (default: True)
        """
        self._group_type = type(self._f["General"])
        self._dataset_type = type(self._f["General/HistoryTable"])

        self._read_master_dates()
        self._read_master_units()
        self._read_master_component_table()
        self._read_master_properties()
        self._get_grid_sizes()

        if read_elements:
            for element in self._element_types:
                _ = self.get_elements(element)
                _ = self.get_properties(element)
                _ = self._get_parents(element)
                _ = self._get_connections(element)
                _ = self.get_timesteps(element)
                _ = self.get_days(element)
                _ = self.get_dates(element)

            alias = {"OILRATSC": "QO",
                     "GASRATSC": "QG",
                     "WATRATSC": "QW",
                     "LIQRATSC": "QL",

                     "OILVOLSC": "NP",
                     "GASVOLSC": "GP",
                     "WATVOLSC": "WP",
                     "LIQVOLSC": "LP",

                     "OILRATRC": "QO_RC",
                     "GASRATRC": "QG_RC",
                     "WATRATRC": "QW_RC",
                    #  "LIQRATRC": "QL_RC",

                     "OILSECSU": "VOIP",
                     "ONFRAC": "UPTIME",

                     "ELTSCUM": "ELAPSED",
                     "TSCUTCUM": "TS_CUTS",
                     "DELTIME": "TS_SIZE",

                     }
            for k,v in alias.items():
                self.set_alias(previous_property=k,
                            new_property=v,
                            check_exists=True)

    @_need_read_file  # type: ignore[arg-type]
    def _read_master_dates(self):
        dataset = self._f["General/MasterTimeTable"]
        self._all_days = dict(zip(dataset["Index"], dataset["Offset in days"]))

        def _parse_date(date):
            date_string = str(date)
            integer_part = int(
                date_string.split(".", maxsplit=1)[0]
            )
            decimal_part = float("0." + date_string.split(".")[1])

            parsed_date = datetime.strptime(str(integer_part), "%Y%m%d")
            fraction_of_day = timedelta(days=decimal_part)
            return parsed_date + fraction_of_day

        dataset = self._f["General/MasterTimeTable"]
        self._all_dates = {
            number: _parse_date(date)
            for (number, date) in zip(dataset["Index"], dataset["Date"])
        }

    @_need_read_file  # type: ignore[arg-type]
    def _read_master_units(self):
        dataset = self._f["General/UnitsTable"]
        columns = zip(
            dataset["Index"],
            dataset["Dimensionality"],
            dataset["Internal Unit"],
            dataset["Output Unit"],
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

        dataset = self._f["General/UnitConversionTable"]
        columns = zip(
            dataset["Dimensionality"],
            dataset["Unit Name"],
            dataset["Gain"],
            dataset["Offset"],
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

    @_need_read_file  # type: ignore[arg-type]
    def _read_master_component_table(self):
        if "ComponentTable" in self._f["General"]:
            dataset = self._f["General/ComponentTable"]
            self._component_list = {
                (number + 1): name[0].decode()
                for (number, name) in enumerate(dataset[:])
                # if name[0].decode() != "WATER"
            }
        else:
            self._component_list = {}

    def _replace_components_property_list(self, property_list):
        pattern = re.compile(r"\((\d+)\)")

        def _replace(match):
            number = int(match.group(1))
            return f'({str(self._component_list.get(number, match.group(1)))})'
        if isinstance(property_list, dict):
            return {pattern.sub(_replace, k): v
                    for k, v in property_list.items()}
        return [pattern.sub(_replace, k) for k in property_list]

    @_need_read_file  # type: ignore[arg-type]
    def _read_master_properties(self):
        dataset = self._f["General/NameRecordTable"]
        self._master_property_list = {}
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
                        self._master_property_list[new_keyword] = {
                            "name": name.replace("$C", f" ({c})"),
                            "long name": long_name.replace("$C", f" ({c})"),
                            "dimensionality_string": dimensionality,
                        }
                else:
                    self._master_property_list[keyword] = {
                        "name": name,
                        "long name": long_name,
                        "dimensionality_string": dimensionality,
                    }
        _ = self._master_property_list.pop("")

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

    def _update_properties_units(self):
        for p in self._master_property_list.values():
            p["conversion"] = self._unit_conversion_from_dimensionality(
                p["dimensionality_string"]
            )
            dimen_ = p["dimensionality_string"]
            p["unit"] = self._unit_from_dimensionality(dimen_)

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
        if unit not in self._unit_list[dimensionality]["conversion"]:
            msg1 = "{unit} is not a valid unit for "
            msg2 = f"{self._unit_list[dimensionality]['type']}."
            raise ValueError(msg1+msg2)
        self._unit_list[dimensionality]["current"] = unit
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
        return current_units

    def _get_unit_numbers(self, unit):
        out = []
        for u in self._unit_list:
            for c in self._unit_list[u]["conversion"]:
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
            msg = f"{old_unit} was not found in Master Units Table."
            raise ValueError(msg)

        for u in unit_numbers:
            g, o = self._unit_list[u]["conversion"][old_unit]
            new_gain = g * gain
            new_offset = o * gain + offset
            self._unit_list[u]["conversion"][new_unit] = (new_gain, new_offset)

    def get_property_description(self, property_name):
        """Returns dict with property attributes

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
            msg = f"{property_name} was not found in Master Property Table."
            raise ValueError(msg)
        p = self._master_property_list[property_name]
        return {
            "description": p["name"],
            "long description": p["long name"],
            "unit": p["unit"],
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
            msg = f"{property_name} was not found in Master Property Table."
            raise ValueError(msg)
        return self._master_property_list[property_name]["unit"]

    def _remove_duplicates(self, input_list):
        unique_items = OrderedDict()
        for item in input_list:
            unique_items[item] = None
        return list(unique_items.keys())

    def _get_dataset(self, element_type, dataset_string):
        if element_type == "grid":
            s = f"SpatialProperties/{dataset_string.upper()}"
        else:
            el_type_string = element_type.upper()
            if element_type == "special":
                el_type_string = el_type_string + " HISTORY"
            else:
                el_type_string = el_type_string + "S"
            s = f"TimeSeries/{el_type_string}/{dataset_string}"
        if s in self._f:
            return self._f[s]
        return []
        # msg1 = f"Dataset {dataset_string} not found for "
        # msg2 = f"{element_type}. {s} does not exist."
        # raise ValueError(msg1+msg2)

    @_need_read_file  # type: ignore[arg-type]
    def _get_elements(self, element_type):
        dataset = self._get_dataset(
            element_type=element_type,
            dataset_string="Origins"
        )
        self._element[element_type] = {
            name.decode(): number
            for (number, name) in enumerate(dataset[:])
            if name.decode() != ""
        }

    def get_elements(self, element_type):
        """Get list of elements.

        Parameters
        ----------
        element_type : str
            Element type to be evaluated.

        Raises
        ------
        ValueError
            If an invalid element type is provided.
        """
        if element_type not in self._element_types:
            msg = f'Valid element type: {", ".join(self._element_types)}'
            raise ValueError(msg)
        if element_type not in self._element:
            self._get_elements(element_type=element_type)
        return self._element[element_type]

    @_need_read_file  # type: ignore[arg-type]
    def _get_properties(self, element_type):
        if element_type == "grid":
            self._property[element_type] = self._get_grid_properties()
        else:
            data = self._get_dataset(
                element_type=element_type,
                dataset_string="Variables"
            )
            self._property[element_type] = {
                name.decode(): number
                for (number, name) in enumerate(data[:])
            }
        self._property[element_type] = self._replace_components_property_list(
            self._property[element_type]
        )

    def get_properties(self, element_type):
        """Get list of properties.

        Parameters
        ----------
        element_type : str
            Element type to be evaluated.

        Raises
        ------
        ValueError
            If an invalid element type is provided.
        """
        if element_type not in self._element_types:
            msg = f'Valid element type: {", ".join(self._element_types)}'
            raise ValueError(msg)
        if element_type not in self._property:
            self._get_properties(element_type=element_type)
        return self._property[element_type]

    def set_alias(self, previous_property, new_property, check_exists=True):
        """Sets an alias for an existing property.

        Parameters
        ----------
        previous_property : str
            Original property.
        new_property : str
            New property alias.
        check_exists : bool, optional
            Checks if new property already exists
            (default: True)

        Raises
        ------
        ValueError
            If previous property is not found.
        ValueError
            If new property already exists and check_exists=True.
        """
        if check_exists:
            for element in self._element_types:
                if new_property in self.get_properties(element):
                    msg = f'Property already exists: {new_property}'
                    raise ValueError(msg)

        # ok = False
        for element in self._element_types:
            if previous_property in self.get_properties(element):
                self._property[element][new_property] = self._property[element][previous_property]
                self._master_property_list[new_property] = self._master_property_list[previous_property]
                # ok = True
        # if not ok:
            # msg = f'Property not found: {previous_property}'
            # print(msg)
            # raise ValueError(msg)

    @_need_read_file  # type: ignore[arg-type]
    def _get_timesteps(self, element_type):
        if element_type == "grid":
            self._timestep[element_type] = self._get_grid_timesteps()
        else:
            dataset = self._get_dataset(
                element_type=element_type, dataset_string="Timesteps"
            )
            self._timestep[element_type] = dataset[:]

    def get_timesteps(self, element_type=None):
        """Get list of time-steps.

        Parameters
        ----------
        element_type : str, optional
            Element type to be evaluated.
            (default: all simulation timesteps)

        Raises
        ------
        ValueError
            If an invalid element type is provided.
        """
        if element_type is None:
            return list(range(len(self._all_days)))
        if element_type not in self._element_types:
            msg = f'Valid element type: {", ".join(self._element_types)}'
            raise ValueError(msg)
        if element_type not in self._timestep:
            self._get_timesteps(element_type)
        return self._timestep[element_type]

    def get_days(self, element_type=None):
        """Get list of days.

        Parameters
        ----------
        element_type : str, optional
            Element type to be evaluated.
            (default: all simulation days)

        Raises
        ------
        ValueError
            If an invalid element type is provided.
        """
        if element_type not in self._element_types+[None]:
            msg = f'Valid element type: {", ".join(self._element_types)}'
            raise ValueError(msg)
        if element_type not in self._day:
            timesteps = self.get_timesteps(element_type=element_type)
            if len(timesteps) > 0:
                days = np.vectorize(lambda x: self._all_days[x])(
                    timesteps
                )
                self._day[element_type] = days
            else:
                self._day[element_type] = []
        return self._day[element_type]

    def get_dates(self, element_type=None):
        """Get list of dates.

        Parameters
        ----------
        element_type : str, optional
            Element type to be evaluated.
            (default: all simulation dates)

        Raises
        ------
        ValueError
            If an invalid element type is provided.
        """
        if element_type not in self._element_types+[None]:
            msg = f'Valid element type: {", ".join(self._element_types)}'
            raise ValueError(msg)
        if element_type not in self._date:
            timesteps = self.get_timesteps(element_type=element_type)
            if len(timesteps) > 0:
                dates = np.vectorize(lambda x: self._all_dates[x])(
                    timesteps
                )
                self._date[element_type] = dates
            else:
                self._date[element_type] = []
        return self._date[element_type]

    def day2date(self, day):
        """Returns date associated to day

        Parameters
        ----------
        days : str or [str]
            Day or list of days to be evaluated.
        """
        dates = [t.timestamp() for t in self.get_dates()]

        interp_day2date = interpolate.interp1d(
                self.get_days(),
                dates,
                kind="linear"
            )

        if isinstance(day, list):
            return [datetime.fromtimestamp(int(x)) for x in interp_day2date(day)]
        return datetime.fromtimestamp(int(interp_day2date(day)))

    def date2day(self, date):
        """Returns day associated to date

        Parameters
        ----------
        date : datetime.datetime or [datetime.datetime]
            Date or list of dates to be evaluated.
        """
        dates = [t.timestamp() for t in self.get_dates()]

        if isinstance(date, list):
          date = [t.timestamp() for t in date]
        else:
          date = date.timestamp()

        interp_date2day = interpolate.interp1d(
                dates,
                self.get_days(),
                kind="linear"
            )
        return interp_date2day(date)


    @_need_read_file  # type: ignore[arg-type]
    def _get_parents(self, element_type):
        if element_type in ["well", "group", "layer"]:
            dataset = self._get_dataset(
                element_type=element_type,
                dataset_string=f"{element_type.capitalize()}Table",
            )

            def _name(name, parent):
                if element_type == "layer":
                    return f"{parent.decode()}{{{name.decode()}}}"
                return name.decode()

            self._parent[element_type] = {
                _name(name, parent): parent.decode()
                for (name, parent) in zip(dataset["Name"], dataset["Parent"])
            }
        else:
            self._parent[element_type] = {
                name: "" for name in self.get_elements(element_type)
            }

    def get_parent(self, element_type, element_name):
        """Get parent of an element.

        Parameters
        ----------
        element_type : str
            Element type to be evaluated.

        Raises
        ------
        ValueError
            If an invalid element type is provided.
        """
        if element_type not in self._element_types:
            msg = f'Valid element type: {", ".join(self._element_types)}'
            raise ValueError(msg)
        if element_type not in self._parent:
            self._get_parents(element_type)
        return self._parent[element_type][element_name]

    @_need_read_file  # type: ignore[arg-type]
    def _get_connections(self, element_type):
        if element_type == "layer":
            dataset = self._get_dataset(
                element_type=element_type,
                dataset_string=f"{element_type.capitalize()}Table",
            )

            def _name(name, parent):
                return f"{parent.decode()}{{{name.decode()}}}"

            self._connection[element_type] = {
                _name(name, parent): connection
                for (name, parent, connection) in zip(
                    dataset["Name"], dataset["Parent"], dataset["Connect To"]
                )
            }
        else:
            self._connection[element_type] = {
                name: "" for name in self.get_elements(element_type)
            }

    def get_connection(self, element_type, element_name):
        """Get connection of an element.

        Parameters
        ----------
        element_type : str
            Element type to be evaluated.

        Raises
        ------
        ValueError
            If an invalid element type is provided.
        """
        if element_type not in self._element_types:
            msg = f'Valid element type: {", ".join(self._element_types)}'
            raise ValueError(msg)
        if element_type not in self._connection:
            self._get_connections(element_type)
        return self._connection[element_type][element_name]

    @_need_read_file  # type: ignore[arg-type]
    def _get_grid_sizes(self):
        dataset = self._f["SpatialProperties/000000/GRID"]
        ni = dataset["IGNTID"][0]
        nj = dataset["IGNTJD"][0]
        nk = dataset["IGNTKD"][0]
        n_cells = ni * nj * nk
        n_active = dataset["IPSTCS"].size
        if dataset["IPSTCS"][-1] > ni * nj * nk:
            self._element["grid"]["FRACTURE"] = np.where(
                self._f["SpatialProperties/000000/GRID/IPSTCS"] > ni * nj * nk
            )[0][0]
            n_cells = 2 * n_cells
        self._grid_size = {
            "ni": ni,
            "nj": nj,
            "nk": nk,
            "n_active": n_active,
            "n_cells": n_cells,
        }

    def get_grid_size(self):
        """Get grid sizes.

        Parameters
        ----------
            None
        """
        ni = self._grid_size["ni"]
        nj = self._grid_size["nj"]
        nk = self._grid_size["nk"]
        return ni, nj, nk

    def get_active_cells(self):
        """Get number of active cells.

        Parameters
        ----------
            None
        """
        return self._grid_size["n_active"]

    @_need_read_file  # type: ignore[arg-type]
    def _get_grid_timesteps(self):
        dataset = self._f["SpatialProperties"]
        grid_timestep_list = []
        for key in dataset.keys():
            sub_dataset = self._f[f"SpatialProperties/{key}"]
            if isinstance(sub_dataset, self._group_type):
                grid_timestep_list.append(int(key))
        return np.array(grid_timestep_list)

    def _grid_properties_adjustments(self, grid_property_list):
        # TODO
        # for p,v in grid_property_list.items():
        #     if p in ['DIFRAC','DJFRAC','DKFRAC']:
        #         v['is_internal'] = True
        pass

    @_need_read_file  # type: ignore[arg-type]
    def _get_grid_properties(self):
        dataset = self._f["SpatialProperties/Statistics"]
        grid_property_list = {
            name.decode(): {
                "min": min_,
                "max": max_,
                "timesteps": set(),
                "is_internal": False,
                "is_complete": False,
                "original_name": name.decode().replace("/","%2F")
            }
            for name, min_, max_ in zip(
                dataset["Keyword"], dataset["Min"], dataset["Max"]
            )
        }

        ni = self._grid_size["ni"]
        nj = self._grid_size["nj"]
        nk = self._grid_size["nk"]
        n_active = self._grid_size["n_active"]
        n_cells = ni * nj * nk

        def _list_grid_properties(timestep, set_timestep=None):
            dataset = self._f[f"SpatialProperties/{timestep}"]
            for key in dataset.keys():
                sub_dataset = self._f[f"SpatialProperties/{timestep}/{key}"]
                if not isinstance(sub_dataset, self._dataset_type):
                    continue
                key = key.replace("%2F", "/")
                if key not in grid_property_list:
                    raise ValueError(f"{key} not listed previously!")
                size = sub_dataset.size
                if size not in [n_cells, n_active]:
                    _ = grid_property_list.pop(key)
                    continue
                if "size" in grid_property_list[key]:
                    if grid_property_list[key]["size"] != size:
                        msg = f"Inconsistent grid size for {key}."
                        raise ValueError(msg)
                else:
                    grid_property_list[key]["size"] = size
                    grid_property_list[key]["is_complete"] = (
                        sub_dataset.size == n_cells
                    )
                if set_timestep is None:
                    grid_property_list[key]["timesteps"].add(
                        int(timestep)
                    )
                else:
                    grid_property_list[key]["timesteps"].add(
                        set_timestep
                    )
                    grid_property_list[key]["is_internal"] = True

        _list_grid_properties("000000/GRID", 0)
        for ts in self.get_timesteps(element_type="grid"):
            _list_grid_properties(str(ts).zfill(6))
        for p in grid_property_list.values():
            p["timesteps"] = list(p["timesteps"])
            p["timesteps"].sort()
        self._grid_properties_adjustments(grid_property_list)
        return grid_property_list

    def _concatenate_arrays(self, arr1, arr2):
        if arr1.ndim == 1:
            arr1 = arr1.reshape(-1, 1)
        if arr2.ndim == 1:
            arr2 = arr2.reshape(-1, 1)
        return np.hstack((arr1, arr2))

    def _data_unit_conversion(self,
                              data,
                              property_names,
                              has_dates=True,
                              is_1d=False):
        if isinstance(property_names, str):
            property_names = [property_names]

        i_delta = 0 if has_dates else 1

        n_data_columns = 1 if is_1d else data.shape[1]
        n_properties = 1 if is_1d else len(property_names)
        n_elements = int(n_data_columns / n_properties)
        for i_property, p in enumerate(property_names):
            gain, offset = self._master_property_list[p]["conversion"]
            if gain != 1.0 or offset != 0.0:
                for i_element in range(n_elements):
                    k = i_property + i_element * n_properties - i_delta
                    if is_1d:
                        data[:] = data[:] * gain + offset
                    else:
                        data[:, k] = data[:, k] * gain + offset

    def _get_dataset_2d_data(self, dataset, param1, param2):
        def _ordered_x(x):
            if isinstance(x, list):
                x_ordered = list(set(x)).copy()
                x_ordered.sort()
            return x_ordered

        x1 = _ordered_x(param1)
        x2 = _ordered_x(param2)

        indexes = []
        if len(x1) > len(x2):
            data = dataset[:, x1, x2[0]]
            indexes.extend([(xi, x2[0]) for xi in x1])
            for x in x2[1:]:
                data = self._concatenate_arrays(data, dataset[:, x1, x])
                indexes.extend([(xi, x) for xi in x1])
        else:
            data = dataset[:, x1[0], x2]
            indexes.extend([(x1[0], xi) for xi in x2])
            for x in x1[1:]:
                data = self._concatenate_arrays(data, dataset[:, x, x2])
                indexes.extend([(x, xi) for xi in x2])

        original_index = []
        for p2 in param2:
            for p1 in param1:
                original_index.append((p1, p2))
        order = [indexes.index(x) for x in original_index]

        return data[:, order]

    @_need_read_file  # type: ignore[arg-type]
    def _get_raw_data(
        self, element_type, property_names, element_names=None, index=None
    ):
        if element_names is None:
            element_names = [""]

        def _get_indexes(name_list, index_dict):
            if isinstance(name_list, list):
                return [index_dict[name] for name in name_list]
            return [index_dict[name_list]]

        property_indexes = _get_indexes(
            property_names, self.get_properties(element_type)
        )
        element_indexes = _get_indexes(
            name_list=element_names,
            index_dict=self.get_elements(element_type)
        )
        dataset = self._get_dataset(
            element_type=element_type,
            dataset_string="Data"
        )

        data = self._get_dataset_2d_data(
            dataset=dataset,
            param1=property_indexes,
            param2=element_indexes
        )
        self._data_unit_conversion(data, property_names)

        if index is None:
            return data
        if index == "dates":
            return self._concatenate_arrays(
                self.get_dates(element_type=element_type), data
            )
        if index == "days":
            return self._concatenate_arrays(
                self.get_days(element_type=element_type), data
            )
        if index == "timesteps":
            return self._concatenate_arrays(
                self.get_timesteps(element_type=element_type), data
            )
        raise ValueError(f"Invalid index: {index}.")

    def _get_interp_data(
        self,
        days,
        element_type=None,
        property_names=None,
        element_names=None,
        raw_data=None,
    ):
        if element_names is None:
            element_names = [""]
        if raw_data is None:
            raw_data = self._get_raw_data(
                element_type=element_type,
                property_names=property_names,
                element_names=element_names,
                index="days",
            )
        data = np.array(days)
        for i in range(1, raw_data.shape[1]):
            interp = interpolate.interp1d(
                raw_data[:, 0],
                raw_data[:, i],
                kind="linear"
            )
            y = interp(days)
            data = self._concatenate_arrays(data, y)
        return data

    def _get_data(
        self,
        days=None,
        element_type=None,
        property_names=None,
        element_names=None,
        raw_data=None,
    ):
        if element_type == "grid":
            msg = "To get grid data use 'get_grid_data'."
            raise ValueError(msg)
        if element_names is None:
            element_names = self.get_elements(element_type=element_type)
        if raw_data is None:
            raw_data = self._get_raw_data(
                element_type=element_type,
                property_names=property_names,
                element_names=element_names,
                index="days",
            )
        if days is None:
            data = raw_data
        else:
            data = self._get_interp_data(days=days, raw_data=raw_data)
        return data

    def get_data(self,
                 element_type,
                 property_names,
                 element_names=None,
                 days=None):
        """Returns data for the required element type properties

        Parameters
        ----------
        element type : str
            Element type to be evaluated.
        property_names : [str]
            Properties to be evaluated.
        element_names : [str], optional
            List of elements to be evaluated.
            Returns all elements if None.
            (default: None)
        days : [float], optional
            List of days to return data.
            Returns all timesteps if None.
            (default: None)

        Raises
        ------
        ValueError
            If property_name is not found.
        ValueError
            If element_type is grid and
            day is not a single number.
        """
        if element_type == "grid":
            if days is None:
                msg = "day must be set for 'grid'."
                raise ValueError(msg)
            if isinstance(days, list):
                if len(days) > 1:
                    msg = "Only a single day must be set for 'grid'."
                    raise ValueError(msg)
                days = days[0]
            return self.get_grid_data(
                property_names=property_names,
                day=days,
                element_names=element_names)

        return self._get_data(
            days=days,
            element_type=element_type,
            property_names=property_names,
            element_names=element_names)

    def get_series_order(self, property_names, element_names=None):
        """Returns tuple with the order of the properties requested"""
        if element_names is None:
            element_names = [""]
        if isinstance(property_names, str):
            property_names = [property_names]
        if isinstance(element_names, str):
            element_names = [element_names]

        original_index = []
        for element in element_names:
            for property_ in property_names:
                original_index.append((element, property_))
        return original_index

    @_need_read_file  # type: ignore[arg-type]
    def _get_single_grid_property(self,
                                  property_name,
                                  ts=None,
                                  element_names=None):
        if element_names is None:
            element_names = ["MATRIX"]
        if "FRACTURE" not in self.get_elements("grid"):
            if "FRACTURE" in element_names:
                msg = "Current grid does not have fracture values."
                raise ValueError(msg)

        properties_ = self.get_properties("grid")
        if properties_[property_name]["is_internal"]:
            ts = "000000/GRID"
        else:
            if ts is None:
                ts = 0
            timesteps_ = properties_[property_name]["timesteps"]
            if ts not in timesteps_:
                msg1 = f"Grid property {property_name} does not "
                msg2 = f"have values for timestep {ts}."
                raise ValueError(msg1+msg2)
            ts = str(ts).zfill(6)

        p_name_ = properties_[property_name]["original_name"]
        data = self._get_dataset(
            element_type="grid",
            dataset_string=f"{ts}/{p_name_}",
        )
        data = data[:]
        self._data_unit_conversion(data=data,
                                   property_names=[property_name],
                                   has_dates=False,
                                   is_1d=True)

        ni = self._grid_size["ni"]
        nj = self._grid_size["nj"]
        nk = self._grid_size["nk"]
        size = self.get_properties("grid")[property_name]["size"]
        if size == ni * nj * nk:
            return data[:]
        if "FRACTURE" not in self.get_elements("grid"):
            return data[:]
        if element_names == ["MATRIX", "FRACTURE"]:
            return data[:]
        if element_names == ["MATRIX"]:
            return data[: self.get_elements("grid")["FRACTURE"]]
        if element_names == ["FRACTURE"]:
            return data[self.get_elements("grid")["FRACTURE"]:]
        raise ValueError(f"Invalid option: {element_names}.")

    def _get_grid_data_to_complete(self,
                                   values,
                                   element_names=None,
                                   default=0):
        if element_names is None:
            element_names = ["MATRIX"]
        ni = self._grid_size["ni"]
        nj = self._grid_size["nj"]
        nk = self._grid_size["nk"]

        dtype = values.dtype
        default = np.array(default).astype(dtype)
        new_array = np.full((ni * nj * nk * 2,), default)

        indexes = self._get_single_grid_property(
            property_name="IPSTCS", ts=0, element_names=element_names
        )
        new_array[indexes - 1] = values.reshape(-1)

        if element_names == ["MATRIX"]:
            return new_array[:ni * nj * nk]
        if element_names == ["FRACTURE"]:
            return new_array[ni * nj * nk:]
        if element_names == ["MATRIX", "FRACTURE"]:
            return new_array
        raise ValueError(f'Invalid elements: {", ".join(element_names)}')

    @_need_read_file  # type: ignore[arg-type]
    def _get_multiple_grid_properties(self,
                                      property_names,
                                      ts=None,
                                      element_names=None):
        if element_names is None:
            element_names = ["MATRIX"]
        if isinstance(property_names, str):
            property_names = [property_names]
        properties = self.get_properties("grid")
        is_complete = {
            p: properties[p]["is_complete"] for p in property_names
        }
        any_complete = any(v for v in is_complete.values())
        data = self._get_single_grid_property(
            property_name=property_names[0], ts=ts, element_names=element_names
        )
        if any_complete and not is_complete[property_names[0]]:
            data = self._get_grid_data_to_complete(
                values=data, element_names=element_names
            )
        data = data.reshape(-1, 1)
        for p in property_names[1:]:
            data_new = self._get_single_grid_property(
                property_name=p, ts=ts, element_names=element_names
            )
            if any_complete and not is_complete[p]:
                data_new = self._get_grid_data_to_complete(
                    values=data_new, element_names=element_names
                )
            data = self._concatenate_arrays(data, data_new)
        return data

    @_need_read_file  # type: ignore[arg-type]
    def _get_grid_data_interpolated(self,
                                    property_names,
                                    day=None,
                                    element_names=None):
        if element_names is None:
            element_names = ["MATRIX"]
        if day is None:
            day = 0
        elif day < 0:
            raise ValueError("Negative days are not valid.")
        elif day > self.get_days("grid")[-1]:
            msg1 = f"No data beyond {self.get_days('grid')[-1]} days. "
            msg2 = f"{day} days is not valid."
            raise ValueError(msg1+msg2)

        if isinstance(property_names, str):
            property_names = [property_names]

        def _get_timesteps_for_interpolation(day):
            ts_index = np.where(self.get_days("grid") == day)[0]
            if len(ts_index) > 0:
                ts = self.get_timesteps("grid")[ts_index[0]]
                return ts_index[0], ts, ts
            ts_index = np.where(self.get_days("grid") > day)[0][0]
            ts_a = self.get_timesteps("grid")[ts_index - 1]
            ts_b = self.get_timesteps("grid")[ts_index]
            return ts_index, ts_a, ts_b
        ts_index, ts_a, ts_b = _get_timesteps_for_interpolation(day)

        def _cannot_interpolate_grid_data(property_names, ts):
            if isinstance(property_names, str):
                property_ = self.get_properties("grid")[property_names]
                if property_["is_internal"]:
                    return False
                if ts in property_["timesteps"]:
                    return False
                return True
            not_ok_list = []
            for p in property_names:
                if _cannot_interpolate_grid_data(p, ts):
                    not_ok_list.append(p)
            return not_ok_list

        cannot_interpolate = self._remove_duplicates(
            _cannot_interpolate_grid_data(property_names, ts_a)
            + _cannot_interpolate_grid_data(property_names, ts_b)
        )
        if len(cannot_interpolate) > 0:
            msg1 = "Cannot interpolate the following "
            msg2 = f"properties at {day} days: "
            msg3 = f"{', '.join(cannot_interpolate)}."
            raise ValueError(msg1+msg2+msg3)

        if ts_a == ts_b:
            return self._get_multiple_grid_properties(
                    property_names=property_names,
                    ts=ts_a,
                    element_names=element_names)

        data_a = self._get_multiple_grid_properties(
            property_names=property_names,
            ts=ts_a,
            element_names=element_names)
        data_b = self._get_multiple_grid_properties(
            property_names=property_names,
            ts=ts_b,
            element_names=element_names)

        day_a = self.get_days("grid")[ts_index - 1]
        day_b = self.get_days("grid")[ts_index]

        alfa = (day - day_a) / (day_b - day_a)
        return data_a + alfa * (data_b - data_a)

    def get_grid_data(self,
                      property_names,
                      day=None,
                      element_names=None,
                      return_complete=False,
                      default=0):
        """Returns grid data

        Parameters
        ----------
        property_names : [str]
            Properties to be evaluated.
        element_names : [str], optional
            List of elements to be evaluated.
            Returns all elements if None.
            (default: None)
        days : [float], optional
            List of days to return data.
            Returns all timesteps if None.
            (default: None)
        return_complete: [bool], optional
            Returns array with values for
            all cells.
            (default: False)
        default: [int/float], optional
            Value to be used in the inactive
            cells.
            (default: 0)

        Raises
        ------
        ValueError
            If property_name is not found.
        """
        data= self._get_grid_data_interpolated(
            property_names=property_names,
            day=day,
            element_names=element_names)
        if return_complete:
            return self._get_grid_data_to_complete(
                data,
                element_names=element_names,
                default=default)
        return data
