"""
sr3reader module tests - Dates and Times
"""

from pathlib import Path
from collections import Counter
from datetime import datetime
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


class TestSr3Dates(unittest.TestCase):
    """Tests Sr3Reader dates and times functionalities"""

    def test_read_times(self):
        """Tests reading times and dates"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.dates.get_timesteps()
        true_result = list(range(3609))
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.dates.get_dates("group")
        true_result = datetime.strptime("20181002", "%Y%m%d")
        self.assertEqual(true_result, file_read[0])
        true_result = datetime.strptime("20240803", "%Y%m%d")
        self.assertEqual(true_result, file_read[-1])

        file_read = sr3.dates.get_days("well")
        true_result = 30.
        self.assertEqual(true_result, file_read[0])
        true_result = 2162.
        self.assertEqual(true_result, file_read[-1])

        file_read = sr3.dates.get_days("grid")
        true_result = [0., 30.]
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.dates.day2date(day=735.)
        true_result = datetime.strptime("20200906", "%Y%m%d")
        self.assertEqual(true_result, file_read)

        file_read = sr3.dates.day2date(day=[735.])
        true_result = [datetime.strptime("20200906", "%Y%m%d")]
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.dates.date2day(date=datetime.strptime("20200906", "%Y%m%d"))
        true_result = 735.
        self.assertEqual(true_result, file_read)

        file_read = sr3.dates.date2day(date=[datetime.strptime("20200906", "%Y%m%d")])
        true_result = [735.]
        _test_equal_lists(self, true_result, file_read)


if __name__ == "__main__":
    unittest.main()
