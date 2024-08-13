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
    def is_valid(element_type):
        """Checks if element type is valid.

        Parameters
        ----------
        element_type : str
            Element type.
        """
        return element_type in ElementHandler.valid_elements()


    # def get_table(self, element_type, dataset_string):
    #     """Returns table from sr3 file.

    #     Parameters
    #     ----------
    #     element_type : str
    #         Element type.
    #     dataset_string : str
    #         Dataset string.
    #     """
    #     if element_type == "grid":
    #         s = f"SpatialProperties/{dataset_string.upper()}"
    #     else:
    #         el_type_string = element_type.upper()
    #         if element_type == "special":
    #             el_type_string = el_type_string + " HISTORY"
    #         else:
    #             el_type_string = el_type_string + "S"
    #         s = f"TimeSeries/{el_type_string}/{dataset_string}"
    #     return self.file.get_table(s)