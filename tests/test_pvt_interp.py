"""
Compare PVT interpolation results with the ones from simulation
"""
import unittest

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

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
    plt.savefig(f"./tests/_no_sync/pvt/offending_{key}.png")
    plt.close()


def _save_worst(key, data_dict, interp_values, original_values):
    """Save the n most offending samples to CSV."""
    # Stack all arrays in data_dict, original_values, and interp_values into a single matrix
    arrays = [np.arange(len(original_values.flatten()))]
    arrays += [np.asarray(data_dict[key]).flatten() for key in data_dict]
    arrays += [original_values.flatten(), interp_values.flatten()]
    data = np.stack(arrays, axis=1)
    n = 10000
    diff = np.abs(original_values - interp_values)
    idx = np.argsort(diff)[-n:][::-1]
    offending_samples = data[idx]
    csv_path = f"./tests/_no_sync/pvt/offending_{key}.csv"
    header = ",".join(['IDX'] + list(data_dict.keys()) + ["Original", "Interpolated"])
    np.savetxt(
        csv_path,
        offending_samples,
        delimiter=",",
        header=header,
        comments="")
    return csv_path


class TestTemplate(unittest.TestCase):
    """Tests reading dat files"""


    def test_pvt_interp(self):
        """Check interpolating PVT data"""
        print("\nTest PVT interpolation")
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
                    csv_path = _save_worst(key, {"Rs":rs, "Pres":pres}, interp_values, original_values)
                    _plot_errors(key, interp_values, original_values)
                    print(f"  Worst offending samples saved to {csv_path}")


    def test_pvt_inv(self):
        """Check interpolating the inverse of PVT data"""
        print("\nTest inverse PVT interpolation")
        path = Path('../SimModels/Unisim_iv_2024/dat_bo/base_case_bo.dat')
        pvt = dat_pvt.get_from_dat(path, verbose=False)
        self.assertEqual(len(pvt), 1, "Should read 1 PVT table")

        sr3 = Sr3Reader(path.with_suffix('.sr3'))
        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES", "RS", "BO", "EG", "VISO", "VISG"])

        rs = file_read["RS"].values.flatten()
        pres = file_read["PRES"].values.flatten()

        eg = file_read["EG"].values.flatten()
        pres_eg = dat_pvt.get_eg_inv(pvt[0], eg)

        ug = file_read["VISG"].values.flatten()
        pres_ug = dat_pvt.get_ug_inv(pvt[0], ug)

        bo = file_read["BO"].values.flatten()
        pres_bo = dat_pvt.get_bo_inv(pvt[0], bo, rs)

        uo = file_read["VISO"].values.flatten()
        pres_uo = dat_pvt.get_uo_inv(pvt[0], uo, rs)

        data = np.stack([eg, ug, bo, uo], axis=1).T
        results = np.stack([pres_eg, pres_ug, pres_bo, pres_uo], axis=1).T

        for i, key in enumerate(['EG', 'UG', 'BO', 'UO']):
            corr = np.corrcoef(pres, results[i])[0, 1]
            max_diff = np.max(np.abs(pres - results[i]))
            max_rel_diff = np.max(np.abs(pres - results[i]) / pres)
            print(f"Correlation for {key}: {corr:0.6f}")
            print(f"   Max difference: {max_diff:.6f}")
            print(f"   Max relative diff.: {max_rel_diff*100:.4f}%")
            if max_rel_diff > 0.001:  # Threshold for significant difference
                csv_path = _save_worst(f'inv_{key}', {"Rs":rs, key:data[i]}, results[i], pres)
                _plot_errors(f'inv_{key}', results[i], pres)
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
            plt.plot(
                pvt[0]['sat']['PRES'], pvt[0]['sat'][f'{key.upper()}'],
                'k--', label='Sat. Value', alpha=0.5)
            plt.xlabel('PRES')
            plt.ylabel(key)
            plt.yscale('log')
            plt.title(f'{key} Extrapolation')
            plt.legend(fontsize='small', ncol=2, bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.savefig(f"./tests/_no_sync/pvt/{key.lower()}_extrapolation.png")
            plt.close()


    def test_water_pvt(self):
        """Check interpolating por and water PVT data"""
        print("\nTest por and water PVT interpolation")
        path = Path('../SimModels/Unisim_iv_2024/dat_bo/base_case_bo.dat')
        pvt = dat_pvt.get_from_dat(path, verbose=False)[0]

        sr3 = Sr3Reader(path.with_suffix('.sr3'))
        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES", "POROS", "VISW", "MASDENW"])
        file_read_por = sr3.data.get(
            element_type="grid",
            properties=["POR"], days=[0])

        poros = file_read["POROS"].values.flatten()
        uw = file_read["VISW"].values.flatten()
        rhow = file_read["MASDENW"].values.flatten()
        bw = pvt['denwat'] / rhow

        por = file_read_por["POR"].values.flatten()
        por = np.stack([por] * (poros.shape[0] // por.shape[0]), axis=0).T.flatten()
        pres = file_read["PRES"].values.flatten()
        poros_ = dat_pvt.get_por_mod(pvt, pres) * por
        bw_ = dat_pvt.get_bw(pvt, pres)
        uw_ = dat_pvt.get_uw(pvt, pres)
        rhow_ = dat_pvt.get_rhow(pvt, pres, bw_)

        results = np.stack([poros, bw, uw, rhow], axis=1).T
        results_ = np.stack([poros_, bw_, uw_, rhow_], axis=1).T

        for i, key in enumerate(['Poros', 'Bw', 'Uw', 'rhow']):
            corr = np.corrcoef(results[i], results_[i])[0, 1]
            max_diff = np.max(np.abs(results[i] - results_[i]))
            max_rel_diff = np.max(np.abs(results[i] - results_[i]) / results[i])
            print(f"Correlation for {key}: {corr:0.6f}")
            print(f"   Max difference: {max_diff:.6f}")
            print(f"   Max relative diff.: {max_rel_diff*100:.4f}%")
            if max_rel_diff > 0.001:  # Threshold for significant difference
                csv_path = _save_worst(
                    f'{key}', {"Por": por, "Pres": pres}, results_[i], results[i])
                _plot_errors(f'{key}', results_[i], results[i])
                print(f"  Worst offending samples saved to {csv_path}")


    def test_pvt_equil(self):
        """Check PVT equilibrium pressure"""
        print("\nTest PVT equilibrium pressure")
        path = Path('../SimModels/Unisim_iv_2024/dat_bo/base_case_bo.dat')
        pvt = dat_pvt.get_from_dat(path, verbose=False)[0]

        sr3 = Sr3Reader(path.with_suffix('.sr3'))
        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES", "SO", "SG", "SW", "BO", "EG", "RS", "MASDENW","POROS"])
        file_read_ = sr3.data.get(
            element_type="grid",
            properties=["BLOCKPVOL","POR"], days=[0])

        pres = file_read["PRES"].values.flatten()
        rs = file_read["RS"].values.flatten()
        so = file_read["SO"].values.flatten()
        sg = file_read["SG"].values.flatten()
        sw = file_read["SW"].values.flatten()
        bo = file_read["BO"].values.flatten()
        eg = file_read["EG"].values.flatten()
        poros = file_read["POROS"].values.flatten()
        rhow = file_read["MASDENW"].values.flatten()
        bw = pvt['denwat'] / rhow

        vpor_ref = file_read_["BLOCKPVOL"].values.flatten()
        vpor_ref = np.stack([vpor_ref] * (pres.shape[0] // vpor_ref.shape[0]), axis=0).T.flatten()
        por = file_read_["POR"].values.flatten()
        por = np.stack([por] * (pres.shape[0] // por.shape[0]), axis=0).T.flatten()
        vpor = vpor_ref / por * poros

        vo_std = vpor * so / bo
        vg_std = vpor * sg * eg + vo_std * rs
        vw_std = vpor * sw / bw

        pres_calc = dat_pvt.find_equilibrium(
            pvt, vo_std, vg_std, vw_std, vpor_ref, max_iter=15, tol=1e-6)

        corr = np.corrcoef(pres, pres_calc)[0, 1]
        max_diff = np.max(np.abs(pres - pres_calc))
        max_rel_diff = np.max(np.abs(pres - pres_calc) / pres)
        print(f"Correlation: {corr:0.6f}")
        print(f"   Max difference: {max_diff:.6f}")
        print(f"   Max relative diff.: {max_rel_diff*100:.4f}%")
        if max_rel_diff > 0.001:  # Threshold for significant difference
            in_data = {
                'Rs': rs,
                'So': so,
                'Sg': sg,
                'Sw': sw,
                'Bo': bo,
                'Eg': eg,
                'Bw': bw,
                'Vpor_ref': vpor_ref,
                'Vo_std': vo_std,
                'Vg_std': vg_std,
                'Vw_std': vw_std
            }
            csv_path = _save_worst('Eq_Pres', in_data, pres_calc, pres)
            _plot_errors('Eq_Pres', pres_calc, pres)
            print(f"  Worst offending samples saved to {csv_path}")


if __name__ == '__main__':
    unittest.main()
