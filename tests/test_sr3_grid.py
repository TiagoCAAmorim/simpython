"""
sr3reader module tests - Grid sizes and properties
"""

from pathlib import Path
import unittest

from rsimpy.cmg.sr3reader import Sr3Reader


class TestSr3Grid(unittest.TestCase):
    """Tests Sr3Reader grid functionalities"""

    def test_read_grid_size(self):
        """Tests reading grid sizes"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.grid.get_size("nijk")
        true_result = (47, 39, 291)
        self.assertEqual(true_result, file_read)

        file_read = sr3.grid.get_size("n_active")
        true_result = 67241
        self.assertEqual(true_result, file_read)

        file_read = sr3.grid.get_size("n_cells")
        true_result = 47 * 39 * 291
        self.assertEqual(true_result, file_read)

        file_read = sr3.grid.active2complete(1)
        true_result = 373
        self.assertEqual(true_result, file_read)

        file_read = sr3.grid.active2complete([1])
        true_result = [373]
        self.assertEqual(true_result, file_read)

        file_read = sr3.grid.active2complete([1,3])
        true_result = [373, 2159]
        for t,r in zip(true_result, file_read):
            self.assertEqual(t, r)

        file_read = sr3.grid.complete2active(2205)
        true_result = 4
        self.assertEqual(true_result, file_read)

        file_read = sr3.grid.complete2active([2159])
        true_result = [3]
        self.assertEqual(true_result, file_read)

        file_read = sr3.grid.complete2active([2159, 373, 100])
        true_result = [3, 1, 0]
        for t,r in zip(true_result, file_read):
            self.assertEqual(t, r)

    def test_read_grid_size_2phi(self):
        """Tests reading grid sizes in 2phi model"""

        test_file = Path("tests/sr3/imex_2phi2k.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.grid.get_size("nijk")
        true_result = (4, 2, 1)
        self.assertEqual(true_result, file_read)

        file_read = sr3.grid.get_size("n_active")
        true_result = 14
        self.assertEqual(true_result, file_read)

        file_read = sr3.grid.get_size("n_active_matrix")
        true_result = 7
        self.assertEqual(true_result, file_read)

        file_read = sr3.grid.get_size("n_active_fracture")
        true_result = 7
        self.assertEqual(true_result, file_read)

        file_read = sr3.grid.get_size("n_cells")
        true_result = 4 * 2 * 1 * 2
        self.assertEqual(true_result, file_read)

    def test_read_grid(self):
        """Tests reading grid properties"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.data.get(
            element_type="grid",
            properties=["BLOCKDEPTH", "NET/GROSS"],
            days=0.,
            active_only=False)

        file_read_ = file_read["index"].values
        self.assertEqual(file_read_[-1], sr3.grid.get_size("n_cells"))

        file_read_ = file_read["BLOCKDEPTH"].sel(day=0.).values
        self.assertEqual(len(file_read_), sr3.grid.get_size("n_cells"))

        true_result = [
            5257.2, 5342.5, 5428.7, 5513.8, 5589.9,
            5651.9, 5703.2, 5818.1, 5818.1, 5818.1
        ]
        for i in range(10):
            self.assertAlmostEqual(true_result[i], round(file_read_[i],1))

        file_read_ = file_read["NET/GROSS"].sel(day=0.).values
        for i in range(10):
            self.assertAlmostEqual(0., file_read_[i])

        file_read = sr3.data.get(
            element_type="grid",
            properties=["BLOCKDEPTH", "NET/GROSS"],
            days=0.,
            active_only=True)

        file_read_ = file_read["BLOCKDEPTH"].sel(day=0.).values
        self.assertEqual(len(file_read_), sr3.grid.get_size("n_active"))

        true_result = [
            5507.3, 5494.4, 5515.1, 5484.5, 5509.3,
            5541.7, 5464.5, 5485.2, 5515.4, 5688.3
        ]
        for i in range(10):
            self.assertAlmostEqual(true_result[i], round(file_read_[i],1))

        file_read_ = file_read["NET/GROSS"].sel(day=0.).values
        for i in range(sr3.grid.get_size("n_active")):
            self.assertAlmostEqual(file_read_[i], 1)

        with self.assertRaises(ValueError):
            file_read = sr3.data.get(
                element_type="grid",
                properties="NET/GROSS",
                elements="MATRIX",
                days=30.)

        file_read = sr3.data.get(
            element_type="grid",
            properties="PRES",
            elements="MATRIX",
            days=30.)

        file_read_ = file_read["PRES"].sel(day=30.).values
        true_result = [
            63489.766, 63396.96, 63545.605, 63325.547,
            63504.36, 63737.207, 63181.977, 63330.82,
            63547.914, 64793.88,
        ]
        true_result = [round(t / 98.0665, 3) for t in true_result]
        for i in range(10):
            self.assertAlmostEqual(true_result[i], round(file_read_[i],3))

        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES","SO"],
            elements="MATRIX",
            days=[0., 30.])

        file_read_ = file_read["PRES"].sel(day=30.).values
        for i in range(10):
            self.assertAlmostEqual(true_result[i], round(file_read_[i],3))

        file_read = sr3.data.get(
            element_type="grid",
            properties=["SO","PRES","VISO","Z(CO2)"],
            elements="MATRIX",
            days=10.)
        file_read_ = file_read["VISO"].sel(day=10.).values
        true_result = [
            (2 * 0.38856095 + 0.38856095) / 3,
            (2 * 0.3883772 + 0.3883772) / 3,
            (2 * 0.3886714 + 0.3886714) / 3,
            (2 * 0.3882356 + 0.3882356) / 3,
            (2 * 0.38858983 + 0.38858983) / 3,
            (2 * 0.38904962 + 0.38904962) / 3,
            (2 * 0.38795048 + 0.38795048) / 3,
            (2 * 0.38824606 + 0.38824606) / 3,
            (2 * 0.38867596 + 0.38867596) / 3,
            (2 * 0.39111543 + 0.39111543) / 3,
        ]
        for i in range(10):
            self.assertAlmostEqual(true_result[i], file_read_[i])

    def test_read_grid_2phi2k(self):
        """Tests reading 2phi2k grid properties"""

        test_file = Path("tests/sr3/imex_2phi2k.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.data.get(
            element_type="grid",
            properties=["BLOCKDEPTH", "NET/GROSS"],
            elements=["MATRIX", "FRACTURE"],
            days=0.,
            active_only=False)

        file_read_ = file_read["index"].values
        self.assertEqual(file_read_[-1], sr3.grid.get_size("n_cells"))

        file_read_ = file_read["BLOCKDEPTH"].sel(day=0.).values
        self.assertEqual(len(file_read_), sr3.grid.get_size("n_cells"))

        true_result = [
            3005.500, 3006.500, 3007.500, 3008.500, 3005.500,
            3006.500, 3007.500, 3008.500, 3005.500, 3006.500,
            3007.500, 3008.500, 3005.500, 3006.500, 3007.500,
            3008.500
        ]
        for t,v in zip(true_result, file_read_):
            self.assertAlmostEqual(t, round(v,1))

        file_read = sr3.data.get(
            element_type="grid",
            properties=["BLOCKDEPTH", "NET/GROSS"],
            days=0.,
            active_only=True)

        file_read_ = file_read["NET/GROSS"].sel(day=0.).values
        for v in file_read_:
            self.assertAlmostEqual(1., v)

        file_read_ = file_read["BLOCKDEPTH"].sel(day=0.).values
        self.assertEqual(len(file_read_), sr3.grid.get_size("n_active"))

        true_result = [
            # 3005.500,
            3006.500, 3007.500, 3008.500, 3005.500, 3006.500, 3007.500, 3008.500,
            # 3005.500,
            3006.500, 3007.500, 3008.500, 3005.500, 3006.500, 3007.500, 3008.500
        ]
        for i in range(10):
            self.assertAlmostEqual(true_result[i], round(file_read_[i],1))

        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES", "SO"],
            days=[0., 1096.],
            active_only=True)

        file_read_ = file_read["SO"].sel(day=1096.).values
        true_result = [
            0.53912, 0.52874, 0.51399, 0.64481, 0.62339,
            0.63017, 0.62788, 0.52435, 0.51081, 0.48366,
            0.64181, 0.61585, 0.62052, 0.61545
        ]

        for t,v in zip(true_result, file_read_):
            self.assertAlmostEqual(t, round(v,5))

        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES", "SO"],
            elements="MATRIX",
            days=[0., 1096.],
            active_only=True)
        file_read_ = file_read["SO"].sel(day=1096.).values
        for t,v in zip(true_result[:7], file_read_):
            self.assertAlmostEqual(t, round(v,5))

        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES", "SO"],
            elements="FRACTURE",
            days=[0., 1096.],
            active_only=True)
        file_read_ = file_read["SO"].sel(day=1096.).values
        for t,v in zip(true_result[7:], file_read_):
            self.assertAlmostEqual(t, round(v,5))

        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES", "SO"],
            days=[0., 1096.],
            active_only=False)

        file_read_ = file_read["SO"].sel(day=1096.).values
        true_result = [
            0.00000, 0.53912, 0.52874, 0.51399, 0.64481,
            0.62339, 0.63017, 0.62788, 0.00000, 0.52435,
            0.51081, 0.48366, 0.64181, 0.61585, 0.62052,
            0.61545
        ]

        for t,v in zip(true_result, file_read_):
            self.assertAlmostEqual(t, round(v,5))

        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES", "SO"],
            elements="MATRIX",
            days=[0., 1096.],
            active_only=False)
        file_read_ = file_read["SO"].sel(day=1096.).values
        for t,v in zip(true_result[:8], file_read_):
            self.assertAlmostEqual(t, round(v,5))

        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES", "SO"],
            elements="FRACTURE",
            days=[0., 1096.],
            active_only=False)
        file_read_ = file_read["SO"].sel(day=1096.).values
        for t,v in zip(true_result[8:], file_read_):
            self.assertAlmostEqual(t, round(v,5))


if __name__ == "__main__":
    unittest.main()
