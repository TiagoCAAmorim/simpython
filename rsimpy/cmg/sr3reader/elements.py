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
    read_grid : bool, optional
        If True, reads grid data.
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
    get_children(element_type, element_name, deep_search=True)
        Returns the children of a specified group or well.
    get_layer_data(data_name)
        Returns layer data.
    """

    def __init__(self, sr3_file, units, grid, auto_read=True, read_grid=True):
        self._element = {k:{} for k in ElementHandler.valid_elements()}
        self._parent = {k:{} for k in ElementHandler.valid_elements()}
        self._property = {k:{} for k in ElementHandler.valid_elements()}
        self._layer_data = None
        self._file = sr3_file
        self._units = units
        self._grid = grid

        self._read_grid = read_grid
        if auto_read:
            self.read()

    def read(self):
        """Reads element information."""
        for element_type in ElementHandler.valid_elements():
            if element_type in ['grid', 'layer'] and not self._read_grid:
                continue
            self._get_elements(element_type)
            self._get_parents(element_type)
        if self._read_grid:
            self._get_layer_data()


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
        wells = []
        for child in children:
            wells += self.get_children("well", child)
        return wells


    def _get_layer_data(self):
        """
        Get layer data.

        Returns
        -------
        Dict
            A dictionary with layer data indexed by layer name.
            The dictionary contains the following keys:
                - number (int): layer number
                - cell_str (str): string representation of the cell
                - cell (int): cell number, as complete cell index
                - cell_act (int): cell number, as active cell index
                - parent (str): parent well
                - connection (int): previous layer number
                - perf (bool): True if the layer is perforated
        """
        if self._layer_data is not None:
            return

        dataset = self._file.get_element_table(
            element_type='layer',
            dataset_string="LayerTable",
        )

        self._layer_data = {
            f"{parent.decode()}{{{cell_str.decode()}}}": {
                "number": int(number),
                "cell_str": cell_str.decode(),
                "cell": self._grid.ijk2n(cell_str.decode()),
                "cell_act": self._grid.complete2active(self._grid.ijk2n(cell_str.decode())),
                "parent": parent.decode(),
                "connection": int(connection),
                "perf": int(perf) == 0,
            }
            for (cell_str, parent, number, connection, perf) in zip(
                dataset["Name"],
                dataset["Parent"],
                dataset["Number"],
                dataset["Connect To"],
                dataset["Type"],
            )
        }


    def get_layer_data(self, data_name=None):
        """
        Get layer data.

        Dictionary by layer name of one of the following options:
            - number: layer number (int)
            - cell_str: string representation of the cell (str)
            - cell: cell number, as complete cell index (int)
            - cell_act: cell number, as active cell index (int)
            - parent: parent well (str)
            - connection: previous layer number (int)
            - perf: True if the layer is perforated (bool)

        Connection is the downstream layer (upstream for injectors).
        Large integers mean that the layer is connected to the 'surface'.

        Parameters
        ----------
        data_name : str
            Name of the data to retrieve. If None, returns all data.
            Default is None.

        Returns
        -------
        Dict
            A dictionary with layer data indexed by layer name.
        """
        self._get_layer_data()
        if data_name is None:
            return self._layer_data
        valid_names = ["number", "cell_str", "cell", "cell_act", "parent", "connection", "perf"]
        if data_name is not None and data_name not in valid_names:
            msg = f"Invalid data name: {data_name}. "
            msg += f"Expected one of: {', '.join(valid_names)}."
            raise ValueError(msg)
        return {
            k: v[data_name]
            for k, v in self._layer_data.items()
        }
