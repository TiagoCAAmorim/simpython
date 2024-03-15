"""
sr3reader module tests
"""
from pathlib import Path
from collections import Counter
import unittest

import context  # noqa # pylint: disable=unused-import
from simpython.cmg import sr3reader

def only_in_first(list_1, list_2):
    """Elements only in first list"""
    return list(set(list_1) - set(list_2))

def have_same_elements(list1, list2):
    """Lists have same elements"""
    return Counter(list1) == Counter(list2)

class TestSr3Reader(unittest.TestCase):
    """Tests Sr3Reader functionalities"""

    def test_read_elements(self):
        """Tests reading the elements of a file"""

        def _test_equal(true_result, file_read, partial_true_result=False):
            missing = only_in_first(true_result, file_read)
            surplus = only_in_first(file_read, true_result)
            error_msg = f"Missing elements: {','.join(missing)}; surplus: {','.join(surplus)}"

            if partial_true_result:
                self.assertEqual(missing, [], error_msg)
            else:
                self.assertTrue(have_same_elements(file_read, true_result),error_msg)

        test_file = Path(r'.\tests\sr3\base_case_3a.sr3').resolve()
        sr3_file = sr3reader.Sr3Reader(test_file)

        true_result = ['I11', 'I11-W', 'I12', 'I12-W', 'I13', 'I13-W',
                       'I14', 'I14-W', 'I15', 'I15-W', 'I16', 'I16-W',
                       'I17', 'I17-W',
                       'P11', 'P12', 'P13', 'P14', 'P15', 'P16']
        file_read = sr3_file.get_elements('well').keys()
        _test_equal(true_result, file_read)

        true_result = ['Default-Group-PRO','Default-Group-INJ',
                       'FIELD-PRO','FIELD-INJ',
                       'I-PLAT1-PRO','I-PLAT1-INJ',
                       'I-PLAT-TLD-PRO','I-PLAT-TLD-INJ',
                       'P-PLAT1-PRO','P-PLAT1-INJ',
                       'P-PLAT-TLD-PRO','P-PLAT-TLD-INJ',
                       'PLAT1-PRO','PLAT1-INJ',
                       'PLAT-TLD-PRO','PLAT-TLD-INJ']
        file_read = sr3_file.get_elements('group').keys()
        _test_equal(true_result, file_read)

        true_result = ['FIELD']
        file_read = sr3_file.get_elements('sector').keys()
        _test_equal(true_result, file_read)

        true_result = ['P11{23,25,49}','I11{31,10,40}','P12{12,31,36}','P13{28,24,48}',
                       'P14{36,17,34}','P15{23,20,40}','P16{13,14,41}',
                       'I12{14,18,43}','I13{26,14,36}','I14{23,10,42}','I15{38,9,24}',
                       'I16{12,22,42}','I17{7,26,41}',
                       'I11-W{31,10,40}','I12-W{14,18,43}','I13-W{26,14,36}','I14-W{23,10,42}',
                       'I15-W{38,9,24}','I16-W{12,22,42}','I17-W{7,26,41}']
        file_read = sr3_file.get_elements('layer').keys()
        _test_equal(true_result, file_read, True)

        true_result = ['MATRIX']
        file_read = sr3_file.get_elements('grid').keys()
        _test_equal(true_result, file_read)

        true_result = ['CO2','N2 toCH4','C2HtoNC5','C6ttoC19','C29toC63']
        file_read = sr3_file._component_list.values() # pylint: disable=protected-access
        _test_equal(true_result, file_read)

        print(f'File open calls: {sr3_file._open_calls}') # pylint: disable=protected-access

if __name__ == '__main__':
    unittest.main()
