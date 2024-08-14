"""
Implements class Sr3Reader
"""

from collections import OrderedDict

import numpy as np
from scipy import interpolate  # type: ignore

from .units import UnitHandler
from .grid import GridHandler
from .properties import PropertyHandler
from .sr3 import Sr3Handler
from .dates import DateHandler
from .elements import ElementHandler


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


    def __init__(self, file_path, usual_units=True, auto_read=True):
        """
        Parameters
        ----------
        file_path : str
            Path to grid file.
        usual_units : bool, optional
            Adds some extra units
            and changes current units.
            (default: True)

        Raises
        ------
        FileNotFoundError
            If file is not found.
        """

        self.file = Sr3Handler(file_path)

        self.dates = DateHandler(self.file, auto_read=auto_read)
        self.units = UnitHandler(self.file, auto_read=auto_read)
        self.grid = GridHandler(self.file, self.dates, auto_read=auto_read)
        self.properties = PropertyHandler(self.file, self.units, self.grid, auto_read=auto_read)
        self.elements = ElementHandler(self.file, self.units, self.grid, auto_read=auto_read)

        if usual_units and auto_read:
            self.set_usual_units()


    def read(self):
        """Reads the contents of the sr3 file."""
        self.dates.read()
        self.units.read()
        self.grid.read()
        self.properties.read()
        self.elements.read()


    def set_usual_units(self):
        """Sets some usual units and property aliases."""
        additional_units = [
            ("m3", "MMm3", (1.0e-6, 0.0)),
            ("bbl", "MMbbl", (1.0e-6, 0.0)),
            ("kg/cm2", "kgf/cm2", (1.0, 0.0)),
        ]

        for old, new, (gain, offset) in additional_units:
            self.units.add(old, new, gain, offset)
        self.units.set_current("pressure", "kgf/cm2")

        alias = {
            "OILRATSC": "QO",
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

            "OILSECSU": "VOIP",
            "ONFRAC": "UPTIME",

            "ELTSCUM": "ELAPSED",
            "TSCUTCUM": "TS_CUTS",
            "DELTIME": "TS_SIZE",
            }
        for k,v in alias.items():
            self.properties.set_alias(old=k, new=v, return_error=False)


    def _remove_duplicates(self, input_list):
        unique_items = OrderedDict()
        for item in input_list:
            unique_items[item] = None
        return list(unique_items.keys())


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
            gain, offset = self.properties.conversion(p)
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
            property_names, self.properties.get(element_type)
        )
        element_indexes = _get_indexes(
            name_list=element_names,
            index_dict=self.elements.get(element_type)
        )
        dataset = self.file.get_element_table(
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
                self.dates.get_dates(element_type=element_type), data
            )
        if index == "days":
            return self._concatenate_arrays(
                self.dates.get_days(element_type=element_type), data
            )
        if index == "timesteps":
            return self._concatenate_arrays(
                self.dates.get_timesteps(element_type=element_type), data
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
            element_names = self.elements.get(element_type=element_type)
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


    def _get_single_grid_property(self,
                                  property_name,
                                  ts=None,
                                  element_names=None):
        if element_names is None:
            element_names = ["MATRIX"]
        if isinstance(element_names, str):
            element_names = [element_names]
        if any(e not in ["MATRIX","FRACTURE"] for e in element_names):
            msg = f"Invalid element type: {', '.join(element_names)}. Expected: MATRIX, FRACTURE."
            raise ValueError(msg)
        if not self.grid.has_fracture() and element_names != ["MATRIX"]:
            msg = "Matrix only grid."
            raise ValueError(msg)

        properties_ = self.properties.get("grid")
        if properties_[property_name]["is_internal"]:
            ts = "000000/GRID"
        else:
            if ts is None:
                ts = 0
            if ts not in properties_[property_name]["timesteps"]:
                msg = f"Grid property {property_name} does not "
                msg += f"have values for timestep {ts}."
                raise ValueError(msg)
            ts = str(ts).zfill(6)

        p_name_ = properties_[property_name]["original_name"]
        data = self.file.get_element_table(
            element_type="grid",
            dataset_string=f"{ts}/{p_name_}",
        )
        data = data[:]
        self._data_unit_conversion(data=data,
                                   property_names=[property_name],
                                   has_dates=False,
                                   is_1d=True)

        if not self.grid.has_fracture():
            return data[:]
        if element_names == ["MATRIX", "FRACTURE"]:
            return data[:]

        size = self.properties.get("grid", property_name)["size"]
        if size == self.grid.get_size("n_active"):
            cell_index = self.grid.get_size("n_active_matrix")
        elif size == self.grid.get_size("n_cells"):
            cell_index = int(self.grid.get_size("n_cells") / 2)
        else:
            msg = f"Invalid size for property {property_name}: {size}. "
            msg += f"Expected: {self.grid.get_size('n_active')} or {self.grid.get_size('n_cells')}."
            raise ValueError(msg)

        if element_names == ["MATRIX"]:
            return data[: cell_index]
        if element_names == ["FRACTURE"]:
            return data[cell_index:]


    def _get_grid_data_to_complete(self,
                                   values,
                                   element_names=None,
                                   default=0):
        if element_names is None:
            element_names = ["MATRIX"]
        ni, nj, nk = self.grid.get_size('nijk')

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


    def _get_multiple_grid_properties(self,
                                      property_names,
                                      ts=None,
                                      element_names=None):
        if element_names is None:
            element_names = ["MATRIX"]
        if isinstance(property_names, str):
            property_names = [property_names]
        properties = self.properties.get("grid")
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
        elif day > self.dates.get_days("grid")[-1]:
            msg1 = f"No data beyond {self.dates.get_days('grid')[-1]} days. "
            msg2 = f"{day} days is not valid."
            raise ValueError(msg1+msg2)

        if isinstance(property_names, str):
            property_names = [property_names]

        def _get_timesteps_for_interpolation(day):
            ts_index = np.where(self.dates.get_days("grid") == day)[0]
            if len(ts_index) > 0:
                ts = self.dates.get_timesteps("grid")[ts_index[0]]
                return ts_index[0], ts, ts
            ts_index = np.where(self.dates.get_days("grid") > day)[0][0]
            ts_a = self.dates.get_timesteps("grid")[ts_index - 1]
            ts_b = self.dates.get_timesteps("grid")[ts_index]
            return ts_index, ts_a, ts_b
        ts_index, ts_a, ts_b = _get_timesteps_for_interpolation(day)

        def _cannot_interpolate_grid_data(property_names, ts):
            if isinstance(property_names, str):
                property_ = self.properties.get("grid")[property_names]
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

        day_a = self.dates.get_days("grid")[ts_index - 1]
        day_b = self.dates.get_days("grid")[ts_index]

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
