# sr3reader/data.py
"""
data.py

This module provides functionality for extracting data.

Classes:
--------
DataHandler
    A class to handle data extraction.

Usage Example:
--------------
data_handler = DataHandler()
well_bhp = data_handler.get("well", property="BHP")
"""

# from collections import OrderedDict

import numpy as np
from scipy import interpolate  # type: ignore


class DataHandler:
    """
    A class to handle data extraction.

    Parameters
    ----------
    sr3_file : sr3reader.Sr3Handler
        SR3 file object.

    dates : sr3reader.DateHandler
        Date handler object.
    units : sr3reader.UnitsHandler
        Units handler object.
    grid : sr3reader.GridHandler
        Grid handler object.

    Methods
    -------

    """

    def __init__(self, sr3_reader):
        self._file = sr3_reader.file
        self._dates = sr3_reader.dates
        self._elements = sr3_reader.elements
        self._properties = sr3_reader.properties
        self._units = sr3_reader.units
        self._grid = sr3_reader.grid


    def _concat(self, arr1, arr2):
        if arr1.ndim == 1:
            arr1 = arr1.reshape(-1, 1)
        if arr2.ndim == 1:
            arr2 = arr2.reshape(-1, 1)
        return np.hstack((arr1, arr2))


    def _get_data_matrix(self, dataset, index1, index2):
        def _ordered_x(x):
            x_ordered = list(set(x)).copy()
            x_ordered.sort()
            return x_ordered

        x1 = _ordered_x(index1)
        x2 = _ordered_x(index2)

        indexes = []
        if len(x1) > len(x2):
            data = dataset[:, x1, x2[0]]
            indexes.extend([(xi, x2[0]) for xi in x1])
            for x in x2[1:]:
                data = self._concat(data, dataset[:, x1, x])
                indexes.extend([(xi, x) for xi in x1])
        else:
            data = dataset[:, x1[0], x2]
            indexes.extend([(x1[0], xi) for xi in x2])
            for x in x1[1:]:
                data = self._concat(data, dataset[:, x, x2])
                indexes.extend([(x, xi) for xi in x2])

        original_index = []
        for p2 in index2:
            for p1 in index1:
                original_index.append((p1, p2))
        order = [indexes.index(x) for x in original_index]

        return data[:, order]


    def _get_raw_data(self, element_type, properties, elements=None):
        self._elements.is_valid(element_type, throw_error=True)

        if isinstance(properties, str):
            properties = [properties]
        if isinstance(elements, str):
            elements = [elements]
        if elements is None:
            elements = self._elements.get(element_type).keys()

        properties_dict = self._properties.get(element_type)
        properties_i = [properties_dict[p] for p in properties]

        elements_dict=self._elements.get(element_type)
        elements_i = [elements_dict[e] for e in elements]

        dataset = self._file.get_element_table(
            element_type=element_type,
            dataset_string="Data"
        )

        data = self._get_data_matrix(
            dataset=dataset,
            index1=properties_i,
            index2=elements_i
        )
        return self._data_unit_conversion(data, properties)


    def _get_time_data(self, element_type, index):
        if index == "dates":
            return self._dates.get_dates(element_type=element_type)
        if index == "days":
            return self._dates.get_days(element_type=element_type)
        if index == "timesteps":
            return self._dates.get_timesteps(element_type=element_type)
        raise ValueError(f"Invalid index: {index}.")


    def _remove_duplicates(self, input_list):
        seen = set()
        unique_list = []
        for item in input_list:
            if item not in seen:
                unique_list.append(item)
                seen.add(item)
        return unique_list


    def _data_unit_conversion(self,
                              data,
                              properties):
        if isinstance(properties, str):
            properties = [properties]

        is_1d = len(data.shape) == 1

        n_data_columns = 1 if is_1d else data.shape[1]
        n_properties = 1 if is_1d else len(properties)
        n_elements = int(n_data_columns / n_properties)
        for i_property, p in enumerate(properties):
            gain, offset = self._properties.conversion(p)
            if gain != 1.0 or offset != 0.0:
                for i_element in range(n_elements):
                    k = i_property + i_element * n_properties
                    if is_1d:
                        data[:] = data[:] * gain + offset
                    else:
                        data[:, k] = data[:, k] * gain + offset
        return data


    def _get_interp_data(self, days, element_type, properties, elements):
        raw_data = self._get_raw_data(
            element_type=element_type,
            properties=properties,
            elements=elements,
        )
        all_days = self._get_time_data(element_type, "days")
        data = np.array(days)
        for i in range(raw_data.shape[1]):
            interp = interpolate.interp1d(
                all_days,
                raw_data[:, i],
                kind="linear"
            )
            y = interp(days)
            data = self._concat(data, y)
        return data


    def get(self,
            element_type,
            properties,
            elements=None,
            days=None):
        """Returns data for the required element type properties

        Parameters
        ----------
        element type : str
            Element type to be evaluated.
        properties : [str]
            Properties to be evaluated.
        elements : [str], optional
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
        self._elements.is_valid(element_type, throw_error=True)
        if isinstance(properties, str):
            properties = [properties]
        if elements is None:
            elements = self._elements.get(element_type).keys()
        if isinstance(elements, str):
            elements = [elements]

        if element_type == "grid":
            if days is None:
                msg = "day must be set for 'grid'."
                raise ValueError(msg)
            if isinstance(days, list):
                if len(days) > 1:
                    msg = "Only a single day must be set for 'grid'."
                    raise ValueError(msg)
                days = days[0]
            if not self._grid.has_fracture() and elements != ["MATRIX"]:
                msg = "Matrix only grid."
                raise ValueError(msg)
            return self.get_grid_data(
                properties=properties,
                day=days,
                elements=elements)

        if days is None:
            days = self._get_time_data(element_type, "days")
        return self._get_interp_data(
            days=days,
            element_type=element_type,
            properties=properties,
            elements=elements)


    def get_series_order(self, properties, elements=None):
        """Returns tuple with the order of the properties requested"""
        if elements is None:
            elements = [""]
        if isinstance(properties, str):
            properties = [properties]
        if isinstance(elements, str):
            elements = [elements]

        original_index = []
        for element in elements:
            for property_ in properties:
                original_index.append((element, property_))
        return original_index


    def _get_single_grid_property(self,
                                  property_name,
                                  ts=None,
                                  elements=None):
        if elements is None:
            elements = ["MATRIX"]
        if isinstance(elements, str):
            elements = [elements]
        if any(e not in ["MATRIX","FRACTURE"] for e in elements):
            msg = f"Invalid element type: {', '.join(elements)}. Expected: MATRIX, FRACTURE."
            raise ValueError(msg)
        if not self._grid.has_fracture() and elements != ["MATRIX"]:
            msg = "Matrix only grid."
            raise ValueError(msg)

        properties_ = self._properties.get("grid")
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
        data = self._file.get_element_table(
            element_type="grid",
            dataset_string=f"{ts}/{p_name_}",
        )
        data = data[:]
        self._data_unit_conversion(data=data,
                                   properties=[property_name])

        if not self._grid.has_fracture():
            return data[:]
        if elements == ["MATRIX", "FRACTURE"]:
            return data[:]

        size = self._properties.get("grid", property_name)["size"]
        if size == self._grid.get_size("n_active"):
            cell_index = self._grid.get_size("n_active_matrix")
        elif size == self._grid.get_size("n_cells"):
            cell_index = int(self._grid.get_size("n_cells") / 2)
        else:
            msg = f"Invalid size for property {property_name}: {size}. "
            msg += f"Expected: {self._grid.get_size('n_active')} "
            msg += f"or {self._grid.get_size('n_cells')}."
            raise ValueError(msg)

        if elements == ["MATRIX"]:
            return data[: cell_index]
        if elements == ["FRACTURE"]:
            return data[cell_index:]


    def _get_grid_data_to_complete(self,
                                   values,
                                   elements=None,
                                   default=0):
        if elements is None:
            elements = ["MATRIX"]
        ni, nj, nk = self._grid.get_size('nijk')

        dtype = values.dtype
        default = np.array(default).astype(dtype)
        new_array = np.full((ni * nj * nk * 2,), default)

        indexes = self._get_single_grid_property(
            property_name="IPSTCS", ts=0, elements=elements
        )
        new_array[indexes - 1] = values.reshape(-1)

        if elements == ["MATRIX"]:
            return new_array[:ni * nj * nk]
        if elements == ["FRACTURE"]:
            return new_array[ni * nj * nk:]
        if elements == ["MATRIX", "FRACTURE"]:
            return new_array
        raise ValueError(f'Invalid elements: {", ".join(elements)}')


    def _get_multiple_grid_properties(self,
                                      properties,
                                      ts=None,
                                      elements=None):
        is_complete = {
            p: self._properties.get("grid")[p]["is_complete"] for p in properties
        }
        any_complete = any(v for v in is_complete.values())
        data = self._get_single_grid_property(
            property_name=properties[0], ts=ts, elements=elements
        )
        if any_complete and not is_complete[properties[0]]:
            data = self._get_grid_data_to_complete(
                values=data, elements=elements
            )
        data = data.reshape(-1, 1)
        for p in properties[1:]:
            data_new = self._get_single_grid_property(
                property_name=p, ts=ts, elements=elements
            )
            if any_complete and not is_complete[p]:
                data_new = self._get_grid_data_to_complete(
                    values=data_new, elements=elements
                )
            data = self._concat(data, data_new)
        return data


    def _get_grid_data_interpolated(self,
                                    properties,
                                    day,
                                    elements):
        def _get_timesteps_for_interpolation(day):
            ts_index = np.where(self._dates.get_days("grid") == day)[0]
            if len(ts_index) > 0:
                ts = self._dates.get_timesteps("grid")[ts_index[0]]
                return ts_index[0], ts, ts
            ts_index = np.where(self._dates.get_days("grid") > day)[0][0]
            ts_a = self._dates.get_timesteps("grid")[ts_index - 1]
            ts_b = self._dates.get_timesteps("grid")[ts_index]
            return ts_index, ts_a, ts_b
        ts_index, ts_a, ts_b = _get_timesteps_for_interpolation(day)

        def _cannot_interpolate_grid_data(properties, ts):
            if isinstance(properties, str):
                property_ = self._properties.get("grid")[properties]
                if property_["is_internal"]:
                    return False
                if ts in property_["timesteps"]:
                    return False
                return True
            not_ok_list = []
            for p in properties:
                if _cannot_interpolate_grid_data(p, ts):
                    not_ok_list.append(p)
            return not_ok_list

        cannot_interpolate = self._remove_duplicates(
            _cannot_interpolate_grid_data(properties, ts_a)
            + _cannot_interpolate_grid_data(properties, ts_b)
        )
        if len(cannot_interpolate) > 0:
            msg = "Cannot interpolate the following "
            msg += f"properties at {day} days: "
            msg += f"{', '.join(cannot_interpolate)}."
            raise ValueError(msg)

        if ts_a == ts_b:
            return self._get_multiple_grid_properties(
                    properties=properties,
                    ts=ts_a,
                    elements=elements)

        data_a = self._get_multiple_grid_properties(
            properties=properties,
            ts=ts_a,
            elements=elements)
        data_b = self._get_multiple_grid_properties(
            properties=properties,
            ts=ts_b,
            elements=elements)

        day_a = self._dates.get_days("grid")[ts_index - 1]
        day_b = self._dates.get_days("grid")[ts_index]

        alfa = (day - day_a) / (day_b - day_a)
        return data_a + alfa * (data_b - data_a)


    def get_grid_data(self,
                      properties,
                      day=None,
                      elements=None,
                      return_complete=False,
                      default=0):
        """Returns grid data

        Parameters
        ----------
        properties : [str]
            Properties to be evaluated.
        elements : [str], optional
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
        if elements is None:
            elements = ["MATRIX"]
        elif isinstance(elements, str):
            elements = [elements]
        if isinstance(properties, str):
            properties = [properties]
        if day is None:
            day = 0
        elif day < 0:
            raise ValueError("Negative days are not valid.")
        elif day > self._dates.get_days("grid")[-1]:
            msg = f"No data beyond {self._dates.get_days('grid')[-1]} days. "
            msg += f"{day} days is not valid."
            raise ValueError(msg)

        data= self._get_grid_data_interpolated(
            properties=properties,
            day=day,
            elements=elements)
        if return_complete:
            return self._get_grid_data_to_complete(
                data,
                elements=elements,
                default=default)
        return data
