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

    def __init__(self, sr3_file):
        self._days = {}
        self._dates = {}
        self.file = sr3_file


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
