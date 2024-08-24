"""
Implements class Sr3Reader
"""

from .sr3 import Sr3Handler
from .dates import DateHandler
from .units import UnitHandler
from .grid import GridHandler
from .properties import PropertyHandler
from .elements import ElementHandler
from .data import DataHandler


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
    read()
        Reads the contents of the sr3 file.
    set_usual_units()
        Sets some usual units and property aliases.
    """


    def __init__(self, file_path, usual_units=True, auto_read=True):
        """
        Parameters
        ----------
        file_path : str
            Path to grid file.
        usual_units : bool, optional
            Adds some unit aliases
            and changes some of the current units.
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
        self.data = DataHandler(self)

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
