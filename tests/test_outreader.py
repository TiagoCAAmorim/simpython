"""
outreader module tests
"""
import unittest

import context  # noqa # pylint: disable=unused-import
from rsimpy.cmg.outreader import utils


class TestTemplate(unittest.TestCase):
    """Tests reading out files"""

    def test_file_type(self):
        """Check file type detection"""
        file_path = 'tests/out/test_gem.out'
        file_type = utils.get_file_type(file_path)
        self.assertEqual(file_type, 'GEM')

        file_path = 'tests/out/test_imex.out'
        file_type = utils.get_file_type(file_path)
        self.assertEqual(file_type, 'IMEX')

        file_path = 'tests/out/no_file.out'
        with self.assertRaises(FileNotFoundError):
            utils.get_file_type(file_path)

        file_path = 'tests/gridfiles/RTYPE.geo'
        with self.assertRaises(ValueError):
            utils.get_file_type(file_path)


if __name__ == '__main__':
    unittest.main()
