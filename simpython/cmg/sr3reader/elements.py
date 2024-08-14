# sr3reader/elements.py
"""
elements.py

This module provides functionality for handling elements.

Classes:
--------
ElementHandler
    A class to handle elements.

Usage Example:
--------------
element_handler = ElementHandler()
"""

# from attrdict import AttrDict


class ElementHandler:
    """
    A class to handle elements.

    Attributes
    ----------
    file : str
        The file path of the SR3 file.
    units : str
        The units of measurement used in the SR3 file.
    grid : Grid
        The grid object representing the simulation grid.

    Methods
    -------
    read()
        Reads element information from the SR3 file.
    valid_elements()
        Returns a tuple of valid element types.
    is_valid(element_type, throw_error=False)
        Checks if an element type is valid.
    get(element_type)
        Returns a list of elements of the specified type.
    get_parent(element_type, element_name)
        Returns the parent of a specified element.
    get_connection(element_type, element_name)
        Returns the connection of a specified element.
    """

    def __init__(self, sr3_file, units, grid, auto_read=True):
        self._element = {k:{} for k in ElementHandler.valid_elements()}
        self._parent = {k:{} for k in ElementHandler.valid_elements()}
        self._connection = {k:{} for k in ElementHandler.valid_elements()}
        self._property = {k:{} for k in ElementHandler.valid_elements()}
        self.file = sr3_file
        self.units = units
        self.grid = grid

        if auto_read:
            self.read()

    def read(self):
        """Reads element information."""
        for element_type in ElementHandler.valid_elements():
            self._get_elements(element_type)
            self._get_parents(element_type)
            self._get_connections(element_type)


    @staticmethod
    def valid_elements():
        """Returns valid element types."""
        return (
            "well",
            "group",
            "sector",
            "layer",
            "special",
            "grid"
        )


    @staticmethod
    def is_valid(element_type, throw_error=False):
        """Checks if element type is valid.

        Parameters
        ----------
        element_type : str
            Element type.
        throw_error : bool, optional
            Whether to throw an error if element type is invalid.
        """
        result = element_type in ElementHandler.valid_elements()
        if not result and throw_error:
            msg = f"Invalid element type: {element_type}. "
            msg += f"Expected one of: {', '.join(ElementHandler.valid_elements())}"
            raise ValueError(msg)
        return result


    def _get_elements(self, element_type):
        if element_type == "grid":
            self._element["grid"] = {
                "MATRIX":0,
                "FRACTURE":self.grid.get_size("n_active_matrix")
                }
        else:
            dataset = self.file.get_element_table(
                element_type=element_type,
                dataset_string="Origins"
            )
            if dataset is not None:
                self._element[element_type] = {
                    name.decode(): number
                    for (number, name) in enumerate(dataset[:])
                    if name.decode() != ""
                }
            else:
                self._element[element_type] = {}


    def get(self, element_type):
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
        self.is_valid(element_type, throw_error=True)
        return self._element[element_type]


    def _get_parents(self, element_type):
        if element_type in ["well", "group", "layer"]:
            dataset = self.file.get_element_table(
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
                name: "" for name in self._element[element_type]
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
        self.is_valid(element_type, throw_error=True)
        if element_name not in self._parent[element_type]:
            msg = f"Parent for {element_name} not found."
            raise ValueError(msg)
        return self._parent[element_type][element_name]


    def _get_connections(self, element_type):
        if element_type == "layer":
            dataset = self.file.get_element_table(
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
                name: "" for name in self._element[element_type]
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
        self.is_valid(element_type, throw_error=True)
        if element_name not in self._connection[element_type]:
            msg = f"Connection for {element_name} not found."
            raise ValueError(msg)
        return self._connection[element_type][element_name]
