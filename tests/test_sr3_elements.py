"""
sr3reader module tests - Element hierarchy and structure
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


class TestSr3Elements(unittest.TestCase):
    """Tests Sr3Reader element functionalities"""

    def test_read_elements(self):
        """Tests reading the elements of a file"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file, auto_read=False)
        sr3.read()

        true_result = [
            "I11", "I11-W", "I12", "I12-W", "I13", "I13-W",
            "I14", "I14-W", "I15", "I15-W", "I16", "I16-W",
            "I17", "I17-W",
            "P11", "P12", "P13", "P14", "P15", "P16"
        ]
        file_read = sr3.elements.get("well").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            "Default-Group-PRO", "Default-Group-INJ",
            "FIELD-PRO", "FIELD-INJ",
            "I-PLAT1-PRO", "I-PLAT1-INJ",
            "I-PLAT-TLD-PRO", "I-PLAT-TLD-INJ",
            "P-PLAT1-PRO", "P-PLAT1-INJ",
            "P-PLAT-TLD-PRO", "P-PLAT-TLD-INJ",
            "PLAT1-PRO", "PLAT1-INJ",
            "PLAT-TLD-PRO", "PLAT-TLD-INJ",
        ]
        file_read = sr3.elements.get("group").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = ["FIELD"]
        file_read = sr3.elements.get("sector").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            "P11{23,25,49}", "I11{31,10,40}", "P12{12,31,36}",
            "P13{28,24,48}", "P14{36,17,34}", "P15{23,20,40}",
            "P16{13,14,41}", "I12{14,18,43}", "I13{26,14,36}",
            "I14{23,10,42}", "I15{38,9,24}", "I16{12,22,42}",
            "I17{7,26,41}", "I11-W{31,10,40}", "I12-W{14,18,43}",
            "I13-W{26,14,36}", "I14-W{23,10,42}", "I15-W{38,9,24}",
            "I16-W{12,22,42}", "I17-W{7,26,41}",
        ]
        file_read = sr3.elements.get("layer").keys()
        _test_equal_lists(self, true_result, file_read, True)

        true_result = ["MATRIX"]
        file_read = sr3.elements.get("grid").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            "CO2",
            "N2 toCH4",
            "C2HtoNC5",
            "C6ttoC19",
            "C29toC63",
            "WATER"
        ]
        file_read = sr3.properties.get_components_list().values()
        _test_equal_lists(self, true_result, file_read)

    def test_read_element_hierarchy(self):
        """Tests reading element hierarchy"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.elements.get_parent(
            element_type="group",
            element_name="I-PLAT1-PRO")
        true_result = "PLAT1-PRO"
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_parent(
            element_type="layer",
            element_name="P13{28,24,48}")
        true_result = "P13"
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_parent(
            element_type="well",
            element_name="P13")
        true_result = "P-PLAT1-PRO"
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_parent(
            element_type="grid",
            element_name="MATRIX")
        true_result = ""
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_layer_data(
            data_name="connection")["I11{31,10,76}"]
        true_result = 99
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_layer_data(
            data_name="perf")["P11{23,25,219}"]
        true_result = False
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="group",
            element_name="FIELD-INJ")
        true_result = [
            "Default-Group-INJ",
            "I-PLAT1-INJ",
            "I-PLAT-TLD-INJ",
            "P-PLAT1-INJ",
            "P-PLAT-TLD-INJ",
            "PLAT1-INJ",
            "PLAT-TLD-INJ"
        ]
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="group",
            element_name="PLAT1-PRO")
        true_result = ["I-PLAT1-PRO", "P-PLAT1-PRO"]
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="group",
            element_name="Default-Group-PRO")
        true_result = []
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="well",
            element_name="PLAT1-PRO")
        true_result = sr3.elements.get("well").keys()
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="well",
            element_name="FIELD-PRO")
        true_result = sr3.elements.get("well").keys()
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="well",
            element_name="PLAT1-INJ")
        true_result = []
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="well",
            element_name="I-PLAT1-PRO")
        true_result = [k for k in sr3.elements.get("well").keys() if k[0]=="I"]
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="layer",
            element_name="P11")
        true_result = [k for k in sr3.elements.get("layer").keys() if k[:3]=="P11"]
        _test_equal_lists(self, true_result, file_read)


if __name__ == "__main__":
    unittest.main()
