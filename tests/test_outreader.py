"""
outreader module tests
"""
import unittest

import context  # noqa # pylint: disable=unused-import
from rsimpy.cmg.outreader import wi, utils


class TestTemplate(unittest.TestCase):
    """Tests reading out files"""

    def test_file_type(self):
        """Check file type detection"""
        file_path = 'tests/_no_sync/out/test_gem.out'
        file_type = utils.get_file_type(file_path)
        self.assertEqual(file_type, 'GEM')

        file_path = 'tests/_no_sync/out/test_imex.out'
        file_type = utils.get_file_type(file_path)
        self.assertEqual(file_type, 'IMEX')

        file_path = 'tests/_no_sync/out/no_file.out'
        with self.assertRaises(FileNotFoundError):
            utils.get_file_type(file_path)

        file_path = 'tests/gridfiles/RTYPE.geo'
        with self.assertRaises(ValueError):
            utils.get_file_type(file_path)


    def test_read_wi_gem(self):
        """Check reading of well index"""
        out_wi = wi.OutWI(verbose=False, wi_only=True, encoding='utf-8')
        file_path = 'tests/_no_sync/out/test_gem.out'
        out_wi.process(file_path, prune=False)

        self.assertEqual(len(out_wi.get()), 69)
        self.assertEqual(len(out_wi.get()[('02/08/2024', 2161.99)]['P11']['con_data']), 70)

        table = out_wi.get_table()
        self.assertEqual(table['well'].unique()[0], 'P11')
        self.assertEqual(len(table['well'].unique()), 26)

        out_wi.prune()
        self.assertEqual(len(out_wi.get()), 1)


    def test_read_wi_imex(self):
        """Check reading of well index"""
        out_wi = wi.OutWI(verbose=False, wi_only=True, encoding='utf-8')
        file_path = 'tests/_no_sync/out/test_imex.out'
        out_wi.process(file_path, prune=False)

        self.assertEqual(len(out_wi.get()), 977)
        self.assertEqual(len(out_wi.get()[('01/12/2048', 11048)]['P11']['con_data']), 74)

        table = out_wi.get_table()
        self.assertEqual(table['well'].unique()[0], 'P11')
        self.assertEqual(len(table['well'].unique()), 26)



if __name__ == '__main__':
    unittest.main()
