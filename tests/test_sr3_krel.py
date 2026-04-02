"""
sr3reader module tests - Relative permeability
"""

from pathlib import Path
import unittest

import matplotlib.pyplot as plt
import numpy as np

from rsimpy.cmg.sr3reader import Sr3Reader


class TestSr3Krel(unittest.TestCase):
    """Tests Sr3Reader relative permeability functionalities"""

    def test_read_krel(self):
        """Tests reading relative permeability tables"""

        test_file = Path("tests/sr3/base_case_bo.sr3")
        sr3 = Sr3Reader(test_file)

        file_read_ = sr3.krel.get(2)
        true_result = [
            0.35000, 0.29412, 0.24522, 0.20268, 0.16593, 0.13443, 0.10763,
            0.08506, 0.06624, 0.05073, 0.03812, 0.02802, 0.02007, 0.01395,
            0.00935, 0.00599, 0.00363, 0.00205, 0.00105, 0.00047, 0.00017,
            0.00004, 0.00001, 0.00000, 0.00000, 0.00000,
        ]
        true_result = np.array(true_result)

        for t,v in zip(true_result, file_read_['krow'].values):
            self.assertAlmostEqual(round(t,5), round(v,5))

        true_result = [
            0.18, 0.20, 0.22, 0.24, 0.26, 0.28, 0.30, 0.32, 0.34, 0.36, 0.38, 0.40, 0.42,
            0.44, 0.46, 0.48, 0.50, 0.52, 0.54, 0.56, 0.58, 0.60, 0.62, 0.64, 0.65, 1,00
        ]
        true_result = np.array(true_result)

        for t,v in zip(true_result, file_read_['sw'].values):
            self.assertAlmostEqual(round(t,5), round(v,5))

        # sr3.krel.get(3).to_csv('test_krel.csv')

    def test_calc_krel(self):
        """Tests calculating relative permeability values"""
        test_file = Path("tests/sr3/base_case_bo.sr3")
        sr3 = Sr3Reader(test_file)

        sw = np.array([0.17, 0.18, 0.31, 0.60, 0.70])
        true_result = np.array([0.00000, 0.00000, (0.04042+0.05173)/2, 0.3, (3*0.3+1*1.0)/4])
        file_read_ = sr3.krel.get_krw(1, sw)

        for t,v in zip(true_result, file_read_):
            self.assertAlmostEqual(round(t,4), round(v,4))

        sg = np.array([0.50, 0.42, 0.31, 0.12])
        true_result = np.array([0.20000, 0.20000, (0.1524+0.14295)/2, 0.0571])
        file_read_ = sr3.krel.get_krg(1, sg)

        for t,v in zip(true_result, file_read_):
            self.assertAlmostEqual(round(t,4), round(v,4))

        sw = np.array([0.18, 0.30, 0.60, 0.18, 0.18])
        sg = np.array([0.00, 0.00, 0.00, 0.20, 0.12])
        true_result = np.array([0.25000, 0.06508, 0.0, 0.0188, 0.0651])
        file_read_ = sr3.krel.get_kro(1, sw, sg)

        for t,v in zip(true_result, file_read_):
            self.assertAlmostEqual(round(t,5), round(v,5))

        kr_table = sr3.krel.get(1)

        last_day = sr3.dates.get_days("grid")[-1]
        file_read_ = sr3.data.get(
            element_type="grid",
            properties=["KRSETN","KRO","KRW","KRG","SW","SG"],
            elements="MATRIX",
            days=last_day)

        kr_setn = file_read_["KRSETN"].sel(day=last_day).values
        kro = file_read_["KRO"].sel(day=last_day).values[kr_setn==1]
        krw = file_read_["KRW"].sel(day=last_day).values[kr_setn==1]
        krg = file_read_["KRG"].sel(day=last_day).values[kr_setn==1]
        sw = file_read_["SW"].sel(day=last_day).values[kr_setn==1]
        sg = file_read_["SG"].sel(day=last_day).values[kr_setn==1]

        calc_kro = sr3.krel.get_kro(1, sw, sg)
        calc_krw = sr3.krel.get_krw(1, sw)
        calc_krg = sr3.krel.get_krg(1, sg)

        _, axes = plt.subplots(3,2, figsize=(12,12))
        axes = axes.flatten()

        axes[0].scatter(sw, kro, label='From file', color='blue', s=5)
        axes[0].scatter(sw, calc_kro, label='Calculated', color='red', s=2)
        axes[0].plot(kr_table['sw'], kr_table['krow'], color='green',
                     linestyle='--', marker='o',label='Table')
        axes[0].set_title('Kro vs Sw')
        axes[0].set_xlabel('Sw')
        axes[0].set_ylabel('Kro')
        axes[0].legend()
        axes[0].grid()

        axes[1].scatter(kro, calc_kro, color='red', s=2, alpha=0.5)
        correlation_coeff = np.corrcoef(kro, calc_kro)[0, 1]
        axes[1].set_title(f'Kro (1-R = {1-correlation_coeff:.4g})')
        axes[1].set_xlabel('True')
        axes[1].set_ylabel('Calculated')
        axes[1].grid()

        axes[2].scatter(sw, krw, label='From file', color='blue', s=5)
        axes[2].scatter(sw, calc_krw, label='Calculated', color='red', s=2)
        axes[2].plot(kr_table['sw'], kr_table['krw'], color='green',
                     linestyle='--', marker='o',label='Table')
        axes[2].set_title('Krw vs Sw')
        axes[2].set_xlabel('Sw')
        axes[2].set_ylabel('Krw')
        axes[2].legend()
        axes[2].grid()

        axes[3].scatter(krw, calc_krw, color='red', s=2, alpha=0.5)
        correlation_coeff = np.corrcoef(krw, calc_krw)[0, 1]
        axes[3].set_title(f'Krw (1-R = {1-correlation_coeff:.4g})')
        axes[3].set_xlabel('True')
        axes[3].set_ylabel('Calculated')
        axes[3].grid()

        axes[4].scatter(sg, krg, label='From file', color='blue', s=5)
        axes[4].scatter(sg, calc_krg, label='Calculated', color='red', s=2)
        axes[4].plot(1-kr_table['sl'], kr_table['krg'], color='green',
                     linestyle='--', marker='o',label='Table')
        axes[4].set_title('Krg vs Sg')
        axes[4].set_xlabel('Sg')
        axes[4].set_ylabel('Krg')
        axes[4].legend()
        axes[4].grid()

        axes[5].scatter(krg, calc_krg, color='red', s=2, alpha=0.5)
        correlation_coeff = np.corrcoef(krg, calc_krg)[0, 1]
        axes[5].set_title(f'Krg (1-R = {1-correlation_coeff:.4g})')
        axes[5].set_xlabel('True')
        axes[5].set_ylabel('Calculated')
        axes[5].grid()

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    unittest.main()
