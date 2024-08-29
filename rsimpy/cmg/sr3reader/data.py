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
wells_bhp = data_handler.get("well", property="BHP")
"""

import numpy as np
import xarray as xr
import pandas as pd

from rsimpy.common import utils


class DataHandler:
    """
    A class to handle data extraction.

    Parameters
    ----------
    sr3_reader : sr3reader.Sr3Reader
        SR3 reader object.

    Methods
    -------
    get(element_type, properties, elements=None, days=None):
        Returns data for the required element type properties.
    """

    def __init__(self, sr3_reader):
        self._file = sr3_reader.file
        self._dates = sr3_reader.dates
        self._elements = sr3_reader.elements
        self._properties = sr3_reader.properties
        self._units = sr3_reader.units
        self._grid = sr3_reader.grid


    def get(self,
            element_type,
            properties,
            elements=None,
            days=None,
            active_only=True):
        """Returns data for the required element type properties.

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
        active_only : bool, optional
            If True, returns only active cells.
            Ignored if element_type is not grid.
            (default: True)

        Raises
        ------
        ValueError
            If property_name is not found.
        ValueError
            If element_type is grid and
            day is not a single number.
        """
        properties, elements, days = self._validade_input(
            element_type=element_type,
            properties=properties,
            elements=elements,
            days=days)

        if element_type == "grid":
            return self._get_grid_data(
                properties=properties,
                elements=elements,
                days=days,
                active_only=active_only)

        return self._get_timeseries(
            element_type=element_type,
            properties=properties,
            elements=elements,
            days=days)


# MARK: Validate Input

    def _validade_input(self, element_type,  properties, elements, days):
        self._elements.is_valid(element_type, throw_error=True)
        properties = self._validate_properties(element_type, properties)
        elements = self._validate_elements(element_type, elements)
        days = self._validate_days(element_type, days)

        return properties, elements, days


    def _validate_days(self, element_type, days):
        if days is None:
            return self._dates.get_days(element_type=element_type)
        if not utils.is_iterable(days):
            days = [days]
        if min(days) < 0:
            raise ValueError("Negative days are not valid.")
        if max(days) > self._dates.get_days(element_type=element_type)[-1]:
            msg = f"No data beyond {self._dates.get_days(element_type)[-1]} days. "
            msg += f"{max(days)} days is not valid."
            raise ValueError(msg)
        return days


    def _validate_elements(self, element_type, elements):
        if elements is None:
            elements = list(self._elements.get(element_type).keys())
        elif isinstance(elements, str):
            elements = [elements]
        for e in elements:
            if e not in self._elements.get(element_type):
                msg = f'Element {e} not found for "{element_type}".'
                raise ValueError(msg)
        return elements


    def _validate_properties(self, element_type, properties):
        if isinstance(properties, str):
            properties = [properties]
        elif len(properties) == 0:
            msg = "At least one property must be provided."
            raise ValueError(msg)
        for p in properties:
            if p not in self._properties.get(element_type):
                msg = f'Property {p} not found for "{element_type}".'
                raise ValueError(msg)
        return properties


# MARK: Timeseries Data

    def _get_raw_timeseries(self, dataset, element_type, property_name, elements):
        property_index = self._properties.get(element_type)[property_name]
        elements_index = [self._elements.get(element_type)[e] for e in elements]
        elements_index.sort()
        return dataset[:, property_index, elements_index]


    def _get_interpolated_timeseries(self, raw_data, all_days, days):
        y = []
        for i in range(raw_data.shape[1]):
            y.append(np.interp(days, all_days, raw_data[:, i]).reshape(-1, 1))
        return np.hstack(y)


    def _get_ordered_elements(self, element_type, elements):
        if element_type == "special":
            return [""]
        elements_index = [self._elements.get(element_type)[e] for e in elements]
        paired_elements = list(zip(elements_index, elements))
        paired_elements.sort()
        _, elements_ = zip(*paired_elements)
        return elements_


    def _get_single_timeseries_property(self, dataset, element_type, property_name, elements, days):
        all_days = self._dates.get_days(element_type)

        raw_data = self._get_raw_timeseries(dataset, element_type, property_name, elements)
        data = self._get_interpolated_timeseries(raw_data, all_days, days)

        gain, offset = self._properties.conversion(property_name)
        data = data * gain + offset

        elements_ = self._get_ordered_elements(element_type, elements)
        data_array = xr.DataArray(
            data,
            dims=["day", "element"],
            coords={"day": days, "element": list(elements_)})

        for k, v in self._properties.description(property_name).items():
            data_array.attrs[k] = v
        return data_array


    def _get_timeseries(self, element_type, properties, elements, days):
        xr_dataset = xr.Dataset()
        xr_dataset.attrs["element_type"] = element_type
        xr_dataset.attrs["file"] = self._file.get_filepath()

        xr_dataset["day"] = days
        xr_dataset["date"] = self._dates.day2date(days)

        dataset = self._file.get_element_table(
            element_type=element_type,
            dataset_string="Data")
        for prop in properties:
            data = self._get_single_timeseries_property(
                dataset,
                element_type,
                prop,
                elements,
                days)
            xr_dataset[prop] = data

        return xr_dataset


# MARK: Grid Data

    def _get_raw_grid_property(self, property_name, elements, ts_list):
        y = []
        for ts in ts_list:
            y.append(self._get_single_raw_grid_property(property_name, elements, ts).reshape(-1, 1))
        return np.hstack(y)


    def _get_single_raw_grid_property(self, property_name, elements, ts):
        data = self._get_grid_dataset(property_name, ts)

        if elements == ["MATRIX", "FRACTURE"]:
            return data[:]
        if not self._grid.has_fracture():
            return data[:]

        fracture_index = self._get_property_fracture_index(property_name)
        if elements == ["MATRIX"]:
            return data[: fracture_index]
        return data[fracture_index:]


    def _get_grid_dataset(self, property_name, ts):
        if self._grid.is_internal(property_name):
            ts_str = "000000/GRID"
        else:
            ts_str = str(ts).zfill(6)

        original_name = self._grid.get_property(property_name)["original_name"]
        return self._file.get_element_table(
            element_type="grid",
            dataset_string=f"{ts_str}/{original_name}",
        )[:]


    def _get_property_fracture_index(self, property_name):
        if self._properties.is_complete(property_name):
            return int(self._grid.get_size("n_cells") / 2)
        return self._grid.get_size("n_active_matrix")


    def _get_grid_interpoland_timesteps(self, day):
        grid_timesteps = self._dates.get_timesteps("grid")
        grid_days = self._dates.get_days("grid")
        ts_index = np.where(grid_days == day)[0]
        if len(ts_index) > 0:
            ts = grid_timesteps[ts_index[0]]
            return ts, ts
        ts_index = np.where(grid_days > day)[0][0]
        ts_a = grid_timesteps[ts_index - 1]
        ts_b = grid_timesteps[ts_index]
        return ts_a, ts_b


    def _get_grid_timesteps_list(self, days):
        ts_set = set()
        for day in days:
            ts_set.update(self._get_grid_interpoland_timesteps(day))
        return sorted(ts_set)


    def _get_interpolated_grid_property(self, raw_data, ts_list, days):
        data = []
        for day in days:
            ts_a, ts_b = self._get_grid_interpoland_timesteps(day)
            ts_index = ts_list.index(ts_a)
            if ts_a == ts_b:
                data.append(raw_data[:, ts_index].reshape(-1, 1))
            else:
                ts_index = ts_list.index(ts_a)
                data_a = raw_data[:, ts_index]
                data_b = raw_data[:, ts_index + 1]
                day_a = self._dates.get_days("grid")[ts_index]
                day_b = self._dates.get_days("grid")[ts_index + 1]
                alfa = (day - day_a) / (day_b - day_a)
                data_ = data_a + alfa * (data_b - data_a)
                data.append(data_.reshape(-1, 1))
        return np.hstack(data)


    def _get_single_grid_property(self, property_name, elements, days, active_only):
        ts_list = self._get_grid_timesteps_list(days)
        for ts in ts_list:
            if ts not in self._grid.get_property(property_name)["timesteps"]:
                msg = f"Grid property {property_name} does not "
                msg += f"have values for timestep {ts}."
                raise ValueError(msg)

        raw_data = self._get_raw_grid_property(property_name, elements, ts_list)
        data = self._get_interpolated_grid_property(raw_data, ts_list, days)

        gain, offset = self._properties.conversion(property_name)
        data = data * gain + offset

        is_complete = self._grid.is_complete(property_name)
        if active_only:
            data = self._grid_data_to_active(is_complete, data, elements)
            index = self._grid.get_cell_indexes(False, elements)
        else:
            data = self._grid_data_to_complete(is_complete, data, elements)
            index = self._grid.get_cell_indexes(True, elements)

        data_array = xr.DataArray(
            data,
            dims=["index", "day"],
            coords={"index": index, "day": days})

        for k, v in self._properties.description(property_name).items():
            data_array.attrs[k] = v
        for k, v in self._grid.get_property(property_name).items():
            data_array.attrs[k] = v
        return data_array


    def _get_grid_data(self, properties, elements, days, active_only):
        xr_dataset = xr.Dataset()
        xr_dataset.attrs["element_type"] = "grid"
        xr_dataset.attrs["file"] = self._file.get_filepath()

        xr_dataset["day"] = days
        xr_dataset["date"] = self._dates.day2date(days)

        for prop in properties:
            data = self._get_single_grid_property(
                prop,
                elements,
                days,
                active_only)
            xr_dataset[prop] = data

        return xr_dataset


    def _grid_data_to_complete(self, is_complete, values, elements, default=0):
        if is_complete:
            return values

        n = self._grid.get_size("n_cells")
        dtype = values.dtype
        default = np.array(default).astype(dtype)
        new_shape = (n,) + values.shape[1:]
        new_array = np.full(new_shape, default)

        index = self._grid.get_cell_indexes(False, elements)
        new_array[index - 1] = values

        if elements == ["MATRIX"]:
            return new_array[:self._grid.get_size("n_matrix")]
        if elements == ["FRACTURE"]:
            return new_array[self._grid.get_size("n_matrix"):]
        return new_array


    def _grid_data_to_active(self, is_complete, values, elements):
        if not is_complete:
            return values

        return values[self._grid.get_cell_indexes(False, elements) - 1]


# MARK: Save Data

    def to_csv(self,
               element_type,
               properties,
               elements=None,
               days=None,
               filename=None):
        """Saves data to a CSV file.

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
        filename : str, optional
            Filename to save the data.
            If None, the data is not saved.
            (default: None)
        """
        xr_dataset = self.get(
            element_type=element_type,
            properties=properties,
            elements=elements,
            days=days)
        if filename is not None:
            time_data = np.array([xr_dataset["day"].values, xr_dataset["date"].values])
            df = pd.DataFrame(time_data.T, columns=["day", "date"])

            df['date'] = pd.to_datetime(df['date'])
            df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S.%f')

            columns = [("day","",""), ("date","","")]
            for prop in properties:
                data = xr_dataset[prop].values
                for i, e in enumerate(xr_dataset["element"].values):
                    df[f"{prop}_{e}"] = data[:, i]
                    columns.append((prop, e, xr_dataset[prop].attrs["unit"]))
            df.columns = pd.MultiIndex.from_tuples(columns)
            df.to_csv(filename, index=False)
