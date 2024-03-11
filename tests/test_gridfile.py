"""
gridfile module tests
"""
from pathlib import Path
import tempfile
import shutil
import unittest

import context  # noqa # pylint: disable=unused-import
from simpython.cmg import gridfile


class TestGridFile(unittest.TestCase):
    """Tests GridFile functionalities"""

    def test_read_file(self):
        """Reads data from files"""

        test_file_float = Path(r'.\tests\gridfiles\PERMK.geo').resolve()
        test_file_int = Path(r'.\tests\gridfiles\RTYPE.geo').resolve()

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

        test_file = Path(r'.\tests\gridfiles\PERMK.geo').resolve()
        data = gridfile.GridFile(file_path=test_file)

        try:
            with tempfile.NamedTemporaryFile(suffix='.geo', delete=False) as temp_file:
                data.write(output_file_path=temp_file.name)
                data_new = gridfile.GridFile(file_path=temp_file.name)

                self.assertEqual(data_new.get_number_values(),
                                 data.get_number_values(),
                                 "Should have the same number as original file")
        finally:
            Path(temp_file.name).unlink()

    def test_read_file_error(self):
        """Reading files with errors"""

        test_file = Path(r'.\tests\gridfiles\RTYPE_not_exist.geo').resolve()
        msg = 'Could not catch the "file not found" error.'
        with self.assertRaises(FileNotFoundError, msg=msg):
            data = gridfile.GridFile(file_path=test_file)
            data.read()

        test_file = Path(r'.\tests\gridfiles\RTYPE_error.geo').resolve()
        msg = 'Could not catch the "more than one keyword" error.'
        with self.assertRaises(ValueError, msg=msg):
            _ = gridfile.GridFile(file_path=test_file)

        test_file = Path(r'.\tests\gridfiles\RTYPE_error2.geo').resolve()
        msg = 'Could not catch the "no data" error.'
        with self.assertRaises(ValueError, msg=msg):
            _ = gridfile.GridFile(file_path=test_file)

    def test_transform_all_files(self):
        """Rewrites all grid files in a given folder."""
        temp_dir = Path(tempfile.mkdtemp())
        src_dir = Path(r'.\tests\gridfiles').resolve()
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


if __name__ == '__main__':
    unittest.main()
