"""
sr3reader module tests - Grid coordinates and connections
"""

from pathlib import Path
import unittest

import matplotlib.pyplot as plt
import numpy as np

import context  # noqa # pylint: disable=unused-import
from rsimpy.cmg.sr3reader import Sr3Reader


class TestSr3Coordinates(unittest.TestCase):
    """Tests Sr3Reader coordinates and connections functionalities"""

    def test_read_grid_coordinates(self):
        """Tests reading grid coordinates"""

        test_file = Path("tests/sr3/mini_section/base_case_bo_section.sr3")
        sr3 = Sr3Reader(test_file)

        file_read_ = sr3.grid.coordinates.get(cells=4, face='K-')
        true_result = [
            1934.6487, 1739.5813, 1718.9533, 1913.0129,
            9392.0850, 9416.2911, 9217.9083, 9194.1446,
            5503.5630, 5494.1958, 5461.7588, 5472.3262
        ]
        true_result = np.array(true_result)
        true_result = true_result.reshape((3,4)).T

        for t,v in zip(true_result.flatten(), file_read_.flatten()):
            self.assertAlmostEqual(t, round(v,5))

    def test_read_grid_coordinates_regular(self):
        """Tests reading grid coordinates on a regular grid"""

        test_file = Path("tests/sr3/dat_mini3d/mini3d.sr3")
        sr3 = Sr3Reader(test_file)

        file_read_ = sr3.grid.coordinates.get(cells=[1,sr3.grid.get_size('n_cells')], face='K-')
        true_result = [
            [ 781346.8879,  781154.2190,  781132.4973,  781326.4533,
            7277248.0147, 7277273.3975, 7277074.1553, 7277048.2540,
               5307.6133,    5312.0649,    5312.0737,    5304.7095],
            [ 781108.1643,  780912.6731,  780887.9641,  781085.6613,
            7276875.5967, 7276901.7247, 7276703.0108, 7276676.1817,
               5317.7378,    5327.2085,    5332.0103,    5318.0859]
        ]
        true_result = np.array(true_result)
        true_result = true_result.reshape((2,3,4)).swapaxes(1,2)

        for t,v in zip(true_result.flatten(), file_read_.flatten()):
            self.assertAlmostEqual(t, round(v,5))

    def test_read_connections(self):
        """Tests reading grid connections"""

        test_file = Path("tests/sr3/mini_section/base_case_bo_section.sr3")
        sr3 = Sr3Reader(test_file)

        file_read_ = sr3.connections.get_connections()
        true_result = [
            [3, 4, 2], [6, 3, 2], [3, 7, 3], [4, 8, 3],
            [5, 6, 2], [6, 7, 2], [7, 8, 2]
        ]
        true_result = np.array(true_result)

        for t,v in zip(true_result.flatten(), file_read_.flatten()):
            self.assertEqual(t, v)

        file_read_ = sr3.connections.get_connections(as_active=True)
        true_result = [
            [1, 2, 2], [4, 1, 2], [1, 5, 3], [2, 6, 3],
            [3, 4, 2], [4, 5, 2], [5, 6, 2]
        ]
        true_result = np.array(true_result)

        for t,v in zip(true_result.flatten(), file_read_.flatten()):
            self.assertEqual(t, v)

    def test_calc_transmissibilities(self):
        """Tests calculating grid connections transmissibilities"""

        test_file = Path("tests/sr3/mini_section/base_case_bo_section.sr3")
        sr3 = Sr3Reader(test_file)

        file_read_ = sr3.connections.get_transmissibilities()
        self.assertEqual(len(file_read_), 7, "Expected 7 transmissibilities.")

        file_read_ = sr3.connections.get_transmissibilities(tof=True)
        self.assertEqual(file_read_.shape[0], 7, "Expected 7 values.")
        self.assertEqual(file_read_.shape[1], 2,
                         "Expected 2 columns for transmissibilities and TOF.")

    def test_print_transmissibilities(self):
        """Tests printing grid connections transmissibilities"""

        test_file = Path("tests/sr3/mini_section/base_case_bo_section.sr3")
        sr3 = Sr3Reader(test_file)

        connections = sr3.connections.get_connections()
        file_read_ = sr3.connections.print_sconnect(connections)

        self.assertEqual(len(file_read_), connections.shape[0])

    def test_plot_faces(self):
        """Tests plotting faces"""

        test_file = Path("tests/sr3/mini_section/base_case_bo_section.sr3")
        sr3 = Sr3Reader(test_file)

        faces = sr3.grid.coordinates.get(cells=[5,6,7,8], face='K-')
        axes = sr3.grid.coordinates.plot_planes(faces)

        self.assertEqual(axes.shape[0], 4, "Expected 4 axes.")

        for i in range(4):
            self.assertIsNotNone(axes[i], f"Axis[{i}] was not created.")

        # plt.savefig('./_faces.png')
        plt.close()

        connections = sr3.connections.get_connections()
        axes = sr3.connections.plot_connection(connections[1])

        self.assertEqual(axes.shape[0], 4, "Expected 4 axes.")

        for i in range(4):
            self.assertIsNotNone(axes[i], f"Axis[{i}] was not created.")

        # plt.savefig('./_connection.png')
        plt.close()


if __name__ == "__main__":
    unittest.main()
