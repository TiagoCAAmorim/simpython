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
sr3_handler = Sr3Handler(sr3_file_path)
table = sr3_handler.get_table("General/UnitsTable")
"""

from pathlib import Path
import h5py  # type: ignore


class Sr3Handler:
    """
    A class to handle sr3 files.

    Parameters
    ----------
    file_path : str or Path
        Path to SR3 file.

    Methods
    -------
    is_closed():
        Check if sr3 file is closed.
    is_open():
        Check if sr3 file is open.
    open():
        Manually open sr3 file.
    close(force_close=False):
        Manually close sr3 file.
    get_hdf_elements():
        Returns dict with all groups and databases in file.
    get_table(table_name):
        Returns table from sr3 file.
    """


    def __init__(self, file_path):
        self._file_path = Path(file_path)
        if not self._file_path.is_file():
            raise FileNotFoundError(f"File not found: {self._file_path}")

        self._file = None
        self._open_count = 0
        self._open_calls = 0


    def is_closed(self):
        """Check if sr3 file is closed."""
        return self._file is None


    def is_open(self):
        """Check if sr3 file is open."""
        return not self.is_closed()


    def open(self):
        """Manually open sr3 file."""
        if self.is_closed():
            self._file = h5py.File(self._file_path)
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
                self._file.close()
                self._file = None
            self._open_count -= 1


    def get_hdf_elements(self):
        """Returns dict with all groups and databases in file"""
        self.open()

        sr3_elements = []
        def get_type(name):
            sr3_elements.append((name, type(self.get_table(name))))
        self._file.visit(get_type)

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
        if table_name in self._file:
            table = self._file[table_name]

        # self.close()
        return table


    def get_element_table(self, element_type, dataset_string):
        """Returns table from sr3 file associated to element type.

        Parameters
        ----------
        element_type : str
            Element type.
        dataset_string : str
            Dataset string.
        """
        if element_type == "grid":
            s = f"SpatialProperties/{dataset_string.upper()}"
        else:
            el_type_string = element_type.upper()
            if element_type == "special":
                el_type_string = el_type_string + " HISTORY"
            else:
                el_type_string = el_type_string + "S"
            s = f"TimeSeries/{el_type_string}/{dataset_string}"
        return self.get_table(s)
