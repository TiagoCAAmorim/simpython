# sr3reader/dates.py
"""
dates.py

This module provides functionality for handling dates.

Classes:
--------
DateHandler
    A class to handle dates.

Usage Example:
--------------
date_handler = DateHandler()
"""

from datetime import datetime, timedelta
import numpy as np
from scipy import interpolate  # type: ignore

from .elements import ElementHandler

class DateHandler:
    """
    A class to handle dates.

    Attributes
    ----------
    file : str
        SR3 file object.

    Methods
    -------
    read()
        Reads date information from the SR3 file.
    get_timesteps(element_type=None)
        Get a list of time-steps for the specified element type.
    get_days(element_type=None)
        Get a list of days for the specified element type.
    get_dates(element_type=None)
        Get a list of dates for the specified element type.
    day2date(day)
        Returns the date associated with the given day.
    date2day(date)
        Returns the day associated with the given date.
    """

    def __init__(self, sr3_file, auto_read=True):
        self._days = {k:np.array([]) for k in ElementHandler.valid_elements()}
        self._days['all'] = np.array([])
        self._dates = {k:np.array([]) for k in ElementHandler.valid_elements()}
        self._dates['all'] = np.array([])
        self._dates['timestamp'] = np.array([])
        self._timesteps = {k:np.array([]) for k in ElementHandler.valid_elements()}
        self._timesteps['all'] = np.array([])

        self.file = sr3_file
        if auto_read:
            self.read()


    def read(self):
        """Reads date information."""
        time_table = self.file.get_table("General/MasterTimeTable")
        self._read_master_time_table(time_table)
        for element_type in ElementHandler.valid_elements():
            self._get_timesteps(element_type)
            self._get_days(element_type)
            self._get_dates(element_type)

        v_timestamp = np.vectorize(lambda t: t.timestamp())
        self._dates['timestamp'] = v_timestamp(self._dates['all'])


    def _read_master_time_table(self, dataset):
        self._timesteps['all'] = dataset["Index"]
        self._days['all'] = dataset["Offset in days"]

        def _parse_date(date):
            date_string = str(date)
            integer_part = int(
                date_string.split(".", maxsplit=1)[0]
            )
            decimal_part = float("0." + date_string.split(".")[1])

            parsed_date = datetime.strptime(str(integer_part), "%Y%m%d")
            fraction_of_day = timedelta(days=decimal_part)
            return parsed_date + fraction_of_day

        vectorized_parse_date = np.vectorize(_parse_date)
        self._dates['all'] = vectorized_parse_date(dataset["Date"])


    def _get_timesteps(self, element_type):
        if element_type == "grid":
            self._timesteps[element_type] = self._get_grid_timesteps()
        else:
            dataset = self.file.get_element_table(
                element_type=element_type,
                dataset_string="Timesteps"
            )
            self._timesteps[element_type] = dataset[:]


    def _get_grid_timesteps(self):
        dataset = self.file.get_table("SpatialProperties")
        grid_timestep_list = []
        group_type = type(self.file.get_table("General"))
        for key in dataset.keys():
            sub_dataset = self.file.get_table(f"SpatialProperties/{key}")
            if isinstance(sub_dataset, group_type):
                grid_timestep_list.append(int(key))
        return np.array(grid_timestep_list)


    def _get_days(self, element_type):
        timesteps = self._timesteps[element_type]
        self._days[element_type] = self._days['all'][timesteps]


    def _get_dates(self, element_type):
        timesteps = self._timesteps[element_type]
        self._dates[element_type] = self._dates['all'][timesteps]


    def _get_times(self, time_dict, element_type=None):
        if element_type is None or element_type == 'all':
            return time_dict['all']
        ElementHandler.is_valid(element_type, throw_error=True)
        return time_dict[element_type]


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
        return self._get_times(self._timesteps, element_type)


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
        return self._get_times(self._days, element_type)


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
        return self._get_times(self._dates, element_type)


    def day2date(self, day):
        """Returns date associated to day

        Parameters
        ----------
        days : str or [str]
            Day or list of days to be evaluated.
        """
        interp_day2date = interpolate.interp1d(
                self._days['all'],
                self._dates['timestamp'],
                kind="linear"
            )

        if isinstance(day, list):
            vectorized_datetime = np.vectorize(datetime.fromtimestamp)
            return vectorized_datetime(interp_day2date(day))
        return datetime.fromtimestamp(float(interp_day2date(day)))


    def date2day(self, date):
        """Returns day associated to date

        Parameters
        ----------
        date : datetime.datetime or [datetime.datetime]
            Date or list of dates to be evaluated.
        """
        if isinstance(date, list):
            v_timestamp = np.vectorize(lambda t: t.timestamp())
            date = v_timestamp(date)
        else:
            date = date.timestamp()

        interp_date2day = interpolate.interp1d(
                self._dates['timestamp'],
                self._days['all'],
                kind="linear"
            )
        return interp_date2day(date)
