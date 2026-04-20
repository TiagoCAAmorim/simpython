"""
sr3reader module tests - Units
"""

from pathlib import Path
from collections import Counter
import unittest

from rsimpy.cmg.sr3reader import Sr3Reader


def only_in_first(list_1, list_2):
    """Elements only in first list"""
    return list(set(list_1) - set(list_2))


def have_same_elements(list1, list2):
    """Lists have same elements"""
    return Counter(list1) == Counter(list2)


def _test_equal_lists(self, true_result, file_read, partial_true_result=False):
    missing = only_in_first(true_result, file_read)
    surplus = only_in_first(file_read, true_result)
    error_list = []
    if len(missing) > 0:
        error_list.append(f"\n  Missing: {', '.join([str(a) for a in missing])}")
    if len(surplus) > 0:
        error_list.append(f"\n  Surplus: {', '.join([str(a) for a in surplus])}")
    error_msg = "".join(error_list)

    if partial_true_result:
        self.assertEqual(missing, [], error_msg)
    else:
        self.assertTrue(have_same_elements(file_read, true_result), error_msg)


class TestSr3Units(unittest.TestCase):
    """Tests Sr3Reader units functionalities"""

    def test_read_units(self):
        """Tests reading the units"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        true_result = {
            "time": "day",
            "temperature": "C",
            "pressure": "kgf/cm2",
            "length": "m",
            "property volume": "m3",
            "permeability": "md",
            "mass": "kg",
            "molar mass": "gmole",
            "viscosity": "cp",
            "energy": "J",
            "well liquid volume": "m3",
            "well gas volume": "m3",
            "well rate time": "day",
            "interfacial tension": "dyne/cm",
            "electrical current": "A",
            "electrical power": "J/day",
            "electrical potential": "V",
            "electrical resistance": "ohm",
            "electrical conductivity": "S/m",
            "electrical energy": "J",
            "temperature difference": "C",
            "diffusion/dispersion coeff.": "cm2/s",
            "concentration": "kg/m3",
            "molar concentration": "gmole/m3",
        }
        file_read = sr3.units.get_current()
        _test_equal_lists(self, true_result.keys(), file_read.keys())
        _test_equal_lists(self, true_result.values(), file_read.values())

        sr3.units.set_current(dimensionality="mass",unit="g")
        file_read = sr3.units.get_current()
        self.assertEqual("g", file_read["mass"])
        file_read = sr3.units.get_current("mass")
        self.assertEqual("g", file_read)

        file_read = sr3.units.get_current("7")
        self.assertEqual("g", file_read)
        file_read = sr3.units.get_current("7-8")
        self.assertEqual("g/gmole", file_read)
        file_read = sr3.units.get_current("-7")
        self.assertEqual("1/g", file_read)
        file_read = sr3.units.get_current("")
        self.assertEqual("", file_read)

        sr3.units.add(old="day", new="week", gain=1./7., offset=0.0)
        sr3.units.set_current(dimensionality="well rate time",unit="week")
        file_read = sr3.properties.unit(property_name="OILRATSC")
        self.assertEqual("m3/week", file_read)

        sr3.properties.set_alias(
            old="OILRATSC",
            new="QO",
            return_error=False)
        sr3.units.set_current(dimensionality="well rate time",unit="day")
        file_read = sr3.properties.unit(property_name="QO")
        self.assertEqual("m3/day", file_read)

        with self.assertRaises(ValueError):
            sr3.properties.set_alias(old="OILRATSC", new="QO")

        with self.assertRaises(ValueError):
            sr3.properties.set_alias(old="OILRATSC", new="OILRATRC")


if __name__ == "__main__":
    unittest.main()
