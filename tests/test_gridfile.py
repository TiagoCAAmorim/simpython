"""
gridfile module tests
"""
from pathlib import Path
import tempfile
import shutil
import unittest
import numpy as np

import context  # noqa # pylint: disable=unused-import
from rsimpy.cmg import gridfile


class TestGridFile(unittest.TestCase):
    """Tests GridFile functionalities"""

    def test_read_file(self):
        """Reads data from files"""

        test_file_float = Path('tests/gridfiles/PERMK.geo')
        test_file_int = Path('tests/gridfiles/RTYPE.geo')

        data_float = gridfile.GridFile(file_path=test_file_float)
        data_int = gridfile.GridFile(file_path=test_file_int)

        self.assertEqual(data_float.get_number_values(),
                         533403,
                         "Should read 533403 variables")
        self.assertEqual(data_int.get_number_values(),
                         533403,
                         "Should read 533403 variables")

        self.assertEqual(data_float.get_keyword().strip(),
                         "PERMK ALL",
                         "Should read 'PERMK ALL'")
        self.assertEqual(data_int.get_keyword().strip(),
                         "RTYPE ALL",
                         "Should read 'RTYPE ALL'")

        self.assertEqual(len(data_float.get_comments().split('\n')),
                         4,
                         "Should read 4 lines of comments")
        self.assertEqual(data_int.get_comments(),
                         '',
                         "Should not find any comments")

    def test_write_file(self):
        """Rewrite file"""

        test_file = Path('tests/gridfiles/PERMK.geo')
        data = gridfile.GridFile(file_path=test_file)

        with tempfile.NamedTemporaryFile(suffix='.geo') as temp_file:
            data.write(file_path=temp_file.name)
            data_new = gridfile.GridFile(file_path=temp_file.name)

            self.assertEqual(data_new.get_number_values(),
                                data.get_number_values(),
                                "Should have the same number as original file")

    def test_read_file_error(self):
        """Reading files with errors"""

        test_file = Path('tests/gridfiles/RTYPE_not_exist.geo')
        msg = 'Could not catch the "file not found" error.'
        with self.assertRaises(FileNotFoundError, msg=msg):
            data = gridfile.GridFile(file_path=test_file)
            data.read()

        test_file = Path('tests/gridfiles/RTYPE_error.geo')
        msg = 'Could not catch the "more than one keyword" error.'
        with self.assertRaises(ValueError, msg=msg):
            _ = gridfile.GridFile(file_path=test_file)

        test_file = Path('tests/gridfiles/RTYPE_error2.geo')
        msg = 'Could not catch the "no data" error.'
        with self.assertRaises(ValueError, msg=msg):
            _ = gridfile.GridFile(file_path=test_file)

    def test_transform_all_files(self):
        """Rewrites all grid files in a given folder."""
        temp_dir = Path(tempfile.mkdtemp())
        src_dir = Path('tests/gridfiles')
        for file_path in src_dir.iterdir():
            if file_path.is_file():
                shutil.copy(file_path, temp_dir)

        data = gridfile.GridFile('')
        data.rewrite_all_grid_files(folder_path=temp_dir,
                                    new_suffix='.xxx',
                                    verbose=False)

        count = 0
        for file_path in temp_dir.iterdir():
            if file_path.suffix == '.xxx':
                count += 1

        self.assertEqual(count, 2, "Should have 2 files")

        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    def test_subgrid(self):
        """Test subgrid generated"""

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".geo") as test_file:
            test_file.write("RTYPE ALL\n")
            test_file.write("1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24")
            test_file.seek(0)

            data = gridfile.GridFile(file_path=test_file.name)

            msg = 'Could not catch the "wrong shape" error.'
            with self.assertRaises(ValueError, msg=msg):
                data.set_shape([1,2])
            with self.assertRaises(ValueError, msg=msg):
                data.set_shape([1,2,5])

            ni, nj, nk = (3, 2, 4)
            data.set_shape([ni,nj,nk])
            data.set_shape((ni,nj,nk))

            self.assertEqual(data.n2ijk(0),
                            (1,1,1),
                            "Coordinate should be (1,1,1)")
            self.assertEqual(data.n2ijk(3),
                            (1,2,1),
                            "Coordinate should be (1,2,1)")
            self.assertEqual(data.n2ijk(8),
                            (3,1,2),
                            "Coordinate should be (3,1,2)")

            self.assertEqual(data.ijk2n((3,1,2)),
                            8,
                            "Cell number should be 8")
            self.assertEqual(data.ijk2n(3,1,2),
                            8,
                            "Cell number should be 8")
            self.assertEqual(data.ijk2n(ni,nj,nk),
                            data.get_number_values()-1,
                            "Cell number should be number of values-1")

            with tempfile.NamedTemporaryFile(suffix='.geo') as temp_file:
                data.write(file_path=temp_file.name, coord_range=((2,3),(1,2),(2,3)))
                data_new = gridfile.GridFile(file_path=temp_file.name)

                self.assertEqual(data_new.get_number_values(),
                                8,
                                "Should have 8 values.")

                self.assertTrue(np.array_equal(
                                    data_new.get_values(),
                                    np.array([8, 9, 11, 12, 14, 15, 17, 18])),
                                "Should have [8, 9, 11, 12, 14, 15, 17, 18].")


if __name__ == '__main__':
    unittest.main()
