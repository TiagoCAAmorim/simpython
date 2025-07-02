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
    ax[0].scatter(original_values, interp_values, alpha=0.5, s=10)
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
    plt.savefig(f"./offending_{key}.png")
    plt.close()


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
        """Check interpolating PVT data"""
        path = Path('../SimModels/Unisim_iv_2024/dat_bo/base_case_bo.dat')
        pvt = dat_pvt.get_from_dat(path, verbose=False)
        self.assertEqual(len(pvt), 1, "Should read 1 PVT table")

        sr3 = Sr3Reader(path.with_suffix('.sr3'))
        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES", "RS", "BO", "EG", "VISO", "VISG", "MASDENO", "MASDENG"])

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
                max_diff = np.max(np.abs(original_values - interp_values))
                max_rel_diff = np.max(np.abs(original_values - interp_values)/original_values)
                print(f"Correlation for {key}: {corr:0.6f}")
                print(f"   Max difference: {max_diff:.6f}")
                print(f"   Max relative diff.: {max_rel_diff*100:.4f}%")
                if max_rel_diff > 0.001:  # Threshold for significant difference
                    csv_path = _save_worst(rs, pres, key, interp_values, original_values)
                    _plot_errors(key, interp_values, original_values)
                    print(f"  Worst offending samples saved to {csv_path}")


    def test_pvt_extrap(self):
        """Check extrapolating PVT data"""
        path = Path('../SimModels/Unisim_iv_2024/dat_bo/base_case_bo.dat')
        pvt = dat_pvt.get_from_dat(path, verbose=False)
        self.assertEqual(len(pvt), 1, "Should read 1 PVT table")

        rs = np.linspace(-100, 500, 10)
        pres = np.linspace(-100, 1000, 1000)

        rs_grid, pres_grid = np.meshgrid(rs, pres, indexing='ij')
        rs_flat = rs_grid.flatten()
        pres_flat = pres_grid.flatten()

        data = np.stack([rs_flat, pres_flat], axis=1)
        interp_ = dat_pvt.get_pvt_values(pvt[0], data, check_limits=False)
        print(f'Interpolated {interp_['BO'].shape[0]:,} values.')

        for key, arr in interp_.items():
            if np.isnan(arr).any():
                raise ValueError(f"NaN values found in interpolated array for {key}")
            if np.isinf(arr).any():
                raise ValueError(f"Inf values found in interpolated array for {key}")

        for key in ['BO', 'UO']:
            bo_grid = interp_[key].reshape(len(rs), len(pres))
            plt.figure(figsize=(10, 6))
            for i, rs_val in enumerate(rs):
                plt.plot(pres, bo_grid[i], label=f'RS={rs_val:.1f}')
            plt.plot(pvt[0]['sat']['PRES'], pvt[0]['sat'][f'{key.upper()}'], 'k--', label='Sat. Value', alpha=0.5)
            plt.xlabel('PRES')
            plt.ylabel(key)
            plt.yscale('log')
            plt.title(f'{key} Extrapolation')
            plt.legend(fontsize='small', ncol=2, bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.savefig(f'./{key.lower()}_extrapolation.png')
            plt.close()

if __name__ == '__main__':
    unittest.main()
