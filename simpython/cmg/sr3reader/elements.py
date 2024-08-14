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

    Methods
    -------
    """

    def __init__(self, sr3_file, units, grid):
        self._element = {k:{} for k in ElementHandler.valid_elements()}
        self._property = {k:{} for k in ElementHandler.valid_elements()}
        self.file = sr3_file
        self.units = units
        self.grid = grid
        self.extract()

    def extract(self):
        """Extracts element information."""
        for element_type in ElementHandler.valid_elements():
            self._get_elements(element_type)
            # self._get_properties(element_type)


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
