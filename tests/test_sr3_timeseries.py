"""
sr3reader module tests - Timeseries data and CSV export
"""

from pathlib import Path
from collections import Counter
import unittest
from time import time

import context  # noqa # pylint: disable=unused-import
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


class TestSr3Timeseries(unittest.TestCase):
    """Tests Sr3Reader timeseries functionalities"""

    def test_read_timeseries(self):
        """Tests reading timeseries"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.data.get(
            element_type="well",
            properties="BHP",
            elements="P11",
            days=[30., 1085., 2162.])
        file_read = file_read["BHP"].sel(element="P11").values
        true_result = [60627.83967735492 / 98.0665,
                       55779.152843383265 / 98.0665,
                       52595.77029111726 / 98.0665]
        _test_equal_lists(self, true_result, list(file_read))

        sr3.properties.set_alias(
            old="OILRATSC",
            new="QO",
            return_error=False)
        file_read = sr3.data.get(
            element_type="well",
            properties=["QO","BHP"],
            elements=["P14","P11"],
            days=[30., 1085., 2162.])

        file_read_ = file_read["QO"].sel(element="P14").values
        true_result = [0.0,
                       6325.951742655704,
                       4247.476791690085]
        _test_equal_lists(self, true_result, list(file_read_))

        file_read_ = file_read["BHP"].sel(element="P14").values
        true_result = [62718.11721660964 / 98.0665,
                       47094.053970322144 / 98.0665,
                       45799.42941685654 / 98.0665]
        _test_equal_lists(self, true_result, list(file_read_))

        file_read_ = file_read["QO"].sel(element="P11").values
        true_result = [6246.5344882818345,
                       7404.518299614956,
                       6078.931879073354]
        _test_equal_lists(self, true_result, list(file_read_))

        file_read_ = file_read["BHP"].sel(element="P11").values
        true_result = [60627.83967735492 / 98.0665,
                       55779.152843383265 / 98.0665,
                       52595.77029111726 / 98.0665]
        _test_equal_lists(self, true_result, list(file_read_))

        file_read = sr3.data.get(
            element_type="group",
            properties=["NP"],
            elements=["PLAT1-PRO"],
            days=[(2.*1001.0+1008.99)/3.])
        file_read_ = file_read["NP"].sel(element="PLAT1-PRO").values[0]
        true_result = (2.*166546.69278864737+241094.6563692809)/3.
        self.assertAlmostEqual(true_result, float(file_read_))

        sr3.units.set_current(dimensionality="well liquid volume", unit="MMbbl")
        file_read = sr3.data.get(
            element_type="group",
            properties=["NP"],
            elements=["PLAT1-PRO"],
            days=[(2.*1001.0+1008.99)/3.])
        file_read_ = file_read["NP"].sel(element="PLAT1-PRO").values[0]
        self.assertAlmostEqual(true_result * 6.2898108E-6, float(file_read_))

        file_read = sr3.data.get(
            element_type="special",
            properties="ELAPSED",
            days=[30., 1085., 2162.])

        file_read_ = file_read["ELAPSED"].sel(element="").values
        true_result = [140.862025,
                       431.85733,
                       2677.2224149999997]
        _test_equal_lists(self, true_result, list(file_read_))

        file_read_ = file_read["ELAPSED"].values.flatten()
        true_result = [140.862025,
                       431.85733,
                       2677.2224149999997]
        _test_equal_lists(self, true_result, list(file_read_))

    def test_to_csv(self):
        """Tests saving data to csv"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.data.get(
            element_type="special",
            properties="ELAPSED",
            days=[30., 1085., 2162.])

        file_read.to_csv('test_A.csv')
        self.assertTrue(Path('test_A.csv').is_file())
        Path('test_A.csv').unlink()

        sr3.units.set_current(dimensionality="well liquid volume", unit="bbl")
        sr3.data.to_csv(
            filename='test_B.csv',
            element_type="well",
            properties=["QO","BHP","NP"],
            elements=["P11","P13"])
        self.assertTrue(Path('test_B.csv').is_file())
        Path('test_B.csv').unlink()

        file_read = sr3.data.get(
            element_type="grid",
            properties=["SO","PRES","VISO","Z(CO2)"],
            elements="MATRIX",
            days=[10., 20.])

        file_read.to_csv('test_C.csv')
        self.assertTrue(Path('test_C.csv').is_file())
        Path('test_C.csv').unlink()

    def test_quick_read_timeseries(self):
        """Tests reading timeseries quicker."""
        test_file = Path("tests/sr3/base_case_3a.sr3")

        start = time()
        sr3 = Sr3Reader(test_file)
        file_read = sr3.data.get(
            element_type="well",
            properties="BHP",
            elements="P11",
            days=[30., 1085., 2162.])
        regular = time() - start

        file_read = file_read["BHP"].sel(element="P11").values
        true_result = [60627.83967735492 / 98.0665,
                       55779.152843383265 / 98.0665,
                       52595.77029111726 / 98.0665]
        _test_equal_lists(self, true_result, list(file_read))

        start = time()
        sr3 = Sr3Reader(test_file, read_grid=False)
        file_read = sr3.data.get(
            element_type="well",
            properties="BHP",
            elements="P11",
            days=[30., 1085., 2162.])
        quick = time() - start

        file_read = file_read["BHP"].sel(element="P11").values
        true_result = [60627.83967735492 / 98.0665,
                       55779.152843383265 / 98.0665,
                       52595.77029111726 / 98.0665]
        _test_equal_lists(self, true_result, list(file_read))

        self.assertTrue(
            quick < regular,
            f"Quick read time ({quick:0.4} s) not less than"
            f" regular read time {regular:0.4} s")

if __name__ == "__main__":
    unittest.main()
