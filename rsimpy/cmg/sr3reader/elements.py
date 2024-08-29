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
element_handler = ElementHandler(sr3_file, units_handler, grid_handler)
well_list = element_handler.get("well")
"""


class ElementHandler:
    """
    A class to handle elements.

    Parameters
    ----------
    sr3_file : sr3reader.Sr3Handler
        SR3 file object.
    units : sr3reader.UnitsHandler
        Units handler object.
    grid : sr3reader.GridHandler
        Grid handler object.
    auto_read : bool, optional
        If True, reads date information from the SR3 file.
        (default: True)

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
        self._file = sr3_file
        self._units = units
        self._grid = grid

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
            self._element["grid"] = {"MATRIX":0}
            if self._grid.has_fracture():
                self._element["grid"]["FRACTURE"] = self._grid.get_size("n_active_matrix")
        else:
            dataset = self._file.get_element_table(
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
        """Get dict of elements numbers.

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
            dataset = self._file.get_element_table(
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
            dataset = self._file.get_element_table(
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


    def _get_direct_children(self, element_type, element_name):
        parents = self._parent[element_type]
        return [k for k, v in parents.items() if v == element_name]


    def get_children(self, element_type, element_name, deep_search=True):
        """Get children of a group or well.

        Parameters
        ----------
        element_type : str
            Element type of the children: group,
            well or layer.
        element_name : str
            Parent group or well.
        deep_search : bool, optional
            Whether to get only direct children.
            (default: True)

        Raises
        ------
        ValueError
            If an invalid element type is provided.
        ValueError
            If an invalid element name is provided.
        """
        if element_type in ["group", "layer"]:
            children = self._get_direct_children(element_type, element_name)
            if deep_search and element_type == "group":
                for child in children:
                    children += self.get_children(element_type, child, deep_search=True)
            return children

        children = self._get_direct_children("group", element_name)
        if len(children) == 0:
            return self._get_direct_children("well", element_name)
        else:
            wells = []
            for child in children:
                wells += self.get_children("well", child)
            return wells
