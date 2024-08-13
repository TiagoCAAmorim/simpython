# sr3reader/sr3.py
"""
sr3.py

This module provides functionality for handling sr3 files.

Classes:
--------
Sr3FileHandler
    A class to handle sr3 files.

Usage Example:
--------------
sr3_handler = Sr3Handler()
"""

from pathlib import Path
import h5py  # type: ignore


# def _need_read_file(func):  # pylint: disable=no-self-argument
#     def wrapper(self, *args, **kwargs):
#         self.open()
#         result = func(self, *args, **kwargs)  # pylint: disable=not-callable
#         self.close()
#         return result
#     return wrapper


class Sr3Handler:
    """
    A class to handle sr3 files.

    Attributes
    ----------
    _file_path : str
        File path.

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


    def __init__(self, file_path):
        self._file_path = Path(file_path)
        if not self._file_path.is_file():
            raise FileNotFoundError(f"File not found: {self._file_path}")

        self._f = None
        self._open_count = 0
        self._open_calls = 0


    def is_closed(self):
        """Check if sr3 file is closed."""
        return self._f is None


    def is_open(self):
        """Check if sr3 file is open."""
        return not self.is_closed()


    def open(self):
        """Manually open sr3 file."""
        if self.is_closed():
            self._f = h5py.File(self._file_path)
            self._open_calls += 1
            self._open_count = 0
        self._open_count += 1


    def close(self, force_close=False):
        """Manually close sr3 file."""
        if self.is_closed():
            self._open_count = 0
        else:
            if force_close:
                self._open_count = 1
            if self._open_count == 1:
                self._f.close()
                self._f = None
            self._open_count -= 1


    def get_hdf_elements(self):
        """Returns dict with all groups and databases in file"""
        self.open()

        sr3_elements = []
        def get_type(name):
            sr3_elements.append((name, type(self.get_table(name))))
        self._f.visit(get_type)

        self.close()
        return sr3_elements


    def get_table(self, table_name):
        """Returns table from sr3 file

        Parameters
        ----------
        table_name : str
            Table to be evaluated.
            Returns None if table is not found.
        """
        self.open()

        table = None
        if table_name in self._f:
            table = self._f[table_name]

        # self.close()
        return table
