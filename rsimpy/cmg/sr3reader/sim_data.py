"""
Data class to add functionality to xarray.Dataset.
"""

import xarray as xr
import numpy as np
import pandas as pd


# MARK: Simulation Data

class SimData(xr.Dataset):
    """Custom class to handle simulation data.

    This class inherits from xarray.Dataset and provides
    additional functionality to save data to a CSV file.

    Parameters
    ----------
    xr.Dataset : xarray.Dataset
        xarray dataset object.

    Methods
    -------
    to_csv(filename)
        Saves data to a CSV file.
    """

    __slots__ = ()  # No additional attributes beyond those in xarray.Dataset

    def __init__(self, xr_dataset, *args, **kwargs):
        super().__init__(xr_dataset, *args, **kwargs)

        for attr in xr_dataset.attrs:
            self.attrs[attr] = xr_dataset.attrs[attr]

        for var in xr_dataset.data_vars:
            self[var] = xr_dataset[var]

        for coord in xr_dataset.coords:
            self.coords[coord] = xr_dataset.coords[coord]


    def _timeseries_to_df(self):
        time_data = np.array([self["day"].values, self["date"].values])
        df = pd.DataFrame(time_data.T, columns=["day", "date"])

        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S.%f')

        columns = [("day","",""), ("date","","")]
        for prop in self.data_vars.keys():
            data = self[prop].values
            for i, e in enumerate(self["element"].values):
                df[f"{prop}_{e}"] = data[:, i]
                columns.append((prop, e, self[prop].attrs["unit"]))
        df.columns = pd.MultiIndex.from_tuples(columns)
        return df


    def _krel_to_df(self):
        sl = self["sl"].values
        data = np.array([sl])
        df = pd.DataFrame(data.T, columns=["Sl"])
        for prop in self.data_vars.keys():
            if "g" in prop:
                data = self[prop].values
                df[prop.title()] = data[:]
        df["Sw"] = self["sw"].values
        for prop in self.data_vars.keys():
            if "w" in prop:
                data = self[prop].values
                df[prop.title()] = data[:]
        return df


    def _grid_to_df(self):
        cell_data = np.array([self["index"].values, self["cell"].values])
        df = pd.DataFrame(cell_data.T, columns=["index", "cell"])

        columns = [("index","",""), ("cell","","")]
        for prop in self.data_vars.keys():
            data = self[prop].values
            for i, d in enumerate(self["day"].values):
                df[f"{prop}_{d}"] = data[:, i]
                columns.append((prop, d, self[prop].attrs["unit"]))
        df.columns = pd.MultiIndex.from_tuples(columns)
        return df


    def to_csv(self, filename):
        """Saves data to a CSV file.

        Parameters
        ----------
        filename: str or pathlib.Path
            Filename to save the data.
        """
        if self.attrs["element_type"] == "grid":
            df = self._grid_to_df()
        elif self.attrs["element_type"] == "krel":
            df = self._krel_to_df()
        else:
            df = self._timeseries_to_df()
        df.to_csv(filename, index=False)
