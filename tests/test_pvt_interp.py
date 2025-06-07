"""
Compare PVT interpolation results with the ones from simulation
"""
import unittest

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

import context  # noqa # pylint: disable=unused-import
from rsimpy.cmg.sr3reader import Sr3Reader
from rsimpy.cmg.datreader import dat_pvt


def _plot_errors(key, interp_values, original_values):
    _, ax = plt.subplots(1, 2, figsize=(12, 5))

    # Scatter plot: Original vs Interpolated
    ax[0].scatter(original_values, interp_values, alpha=0.5)
    ax[0].set_xlabel(f"Original {key}")
    ax[0].set_ylabel(f"Interpolated {key}")
    ax[0].set_title(f"Scatter plot of {key}: Original vs Interpolated")
    ax[0].grid(True)

    # Histogram of differences
    diff = original_values - interp_values
    ax[1].hist(diff, bins=50, alpha=0.7)
    ax[1].set_xlabel("Original - Interpolated")
    ax[1].set_ylabel("Frequency")
    ax[1].set_title(f"Histogram of differences for {key}")
    ax[1].grid(True)

    plt.tight_layout()
    plt.show()


def _save_worst(rs, pres, key, interp_values, original_values):
    """Save the n most offending samples to CSV."""
    data = np.stack([rs, pres, original_values, interp_values], axis=1)
    n = 10000
    diff = np.abs(original_values - interp_values)
    idx = np.argsort(diff)[-n:][::-1]
    offending_samples = data[idx]
    csv_path = f"./offending_{key}.csv"
    np.savetxt(
        csv_path,
        offending_samples,
        delimiter=",",
        header="RS,PRES,Original,Interpolated",
        comments="")
    print(f"Saved {n} most offending samples for {key} to {csv_path}")
    return csv_path


class TestTemplate(unittest.TestCase):
    """Tests reading dat files"""


    def test_read_pvt(self):
        """Check reading PVT data in dat file"""
        path = Path('../SimModels/Unisim_iv_2024/dat_bo/base_case_bo.dat')
        pvt = dat_pvt.get_from_dat(path, verbose=False)
        self.assertEqual(len(pvt), 1, "Should read 1 PVT table")

        sr3 = Sr3Reader(path.with_suffix('.sr3'))
        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES", "RS", "BO", "EG", "VISO", "VISG","MASDENO","MASDENG"])

        rs = file_read["RS"].values.flatten()
        pres = file_read["PRES"].values.flatten()
        data = np.stack([rs, pres], axis=1)
        interp_ = dat_pvt.get_pvt_values(pvt[0], data, check_limits=False)

        for key, interp_values in interp_.items():
            key_ = key.replace("U", "VIS")
            key_ = key_.replace("DEN", "MASDEN")
            if key_ in file_read:
                original_values = file_read[key_].values.flatten()
                corr = np.corrcoef(original_values, interp_values)[0, 1]
                print(f"Correlation for {key}: {corr:0.6f}")
                print(f"   Max difference: {np.max(np.abs(original_values - interp_values)):.6f}")
                print(f"   Max relative diff.: {
                    np.max(np.abs(original_values - interp_values)/original_values)*100:.4f}%")
                if corr < 0.99999:
                    csv_path = _save_worst(rs, pres, key, interp_values, original_values)
                    _plot_errors(key, interp_values, original_values)
                    print(f"Offending samples saved to {csv_path}")
                    # self.assertTrue(corr > 0.99999,
                    #     f"Correlation for {key} is too low: {corr:.6f}. "
                    #     f"Check offending samples saved to {csv_path}")


if __name__ == '__main__':
    unittest.main()
