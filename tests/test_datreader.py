"""
outreader module tests
"""
import unittest

from pathlib import Path
import context  # noqa # pylint: disable=unused-import
from rsimpy.cmg.datreader import dat_dates, dat_parser, dat_run, sch_to_daily, dat_pvt
import os
import numpy as np


def compare_files(file1, file2):
    """Compare the contents of two text files."""
    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        content1 = f1.read()
        content2 = f2.read()
        return content1 == content2


class TestTemplate(unittest.TestCase):
    """Tests reading dat files"""

    def test_read_dat_keys(self):
        """Check reading keywords in dat file"""

        parser = dat_parser.DatParser(
            encoding='utf-8',
            ignore=['TITLE1', 'GRID',
                    'VFP_keys', 'GRID_keys', 'FLUID_keys',
                    'TRIGGER_keys', 'KREL_keys', 'WELL_keys'],
            verbose=False,
            _debug=True
        )

        folder = Path('tests/_no_sync/ex/dat/')

        parser.process(folder / 'base_case_bo.dat')
        results = parser.get()

        self.assertTrue('GRID' in results, "No GRID data found")
        self.assertTrue('RUN' in results, "No RUN data found")

        run_keys = [v[0] for v in results['RUN']]
        self.assertTrue('DATE' in run_keys, "No DATE in RUN section")


    def test_read_save_load(self):
        """Check save and load of dat file keywords"""

        parser = dat_parser.DatParser(
            encoding='utf-8',
            ignore=['TITLE1', 'GRID',
                    'VFP_keys', 'GRID_keys', 'FLUID_keys',
                    'TRIGGER_keys', 'KREL_keys', 'WELL_keys'],
            verbose=False,
            _debug=True
        )

        folder = Path('tests/_no_sync/ex/dat/')

        parser.process(folder / 'base_case_bo.dat')
        parser.save(folder / 'base_case_bo.json')

        dat_parser2 = dat_parser.DatParser(verbose=False, _debug=True)
        dat_parser2.load(folder / 'base_case_bo.json')
        dat_parser2.save(folder / 'base_case_bo_bk.json')

        compare = compare_files(
            folder / 'base_case_bo.json',
            folder / 'base_case_bo_bk.json')
        self.assertTrue(compare, "The files are not the same")


    def test_read_dates(self):
        """Check reading dates in dat file"""

        folder = Path('tests/_no_sync/ex/dat/')
        file = folder / 'base_case_bo.dat'

        dates = dat_dates.get_from_dat(file)

        self.assertEqual(len(dates), 955, "Should read 955 DATES")
        self.assertEqual(
            dat_dates.to_str(dates[0]),
            '2018 09 02',
            "First date is not correct")
        self.assertEqual(
            dat_dates.to_str(dates[-1]),
            '2049 01 01',
            "Last date is not correct")


    def test_read_log_dates(self):
        """Check reading dates in out file"""

        folder = Path('tests/_no_sync/ex/dat/')
        file = folder / 'base_case_bo_small.out'

        dates = dat_dates.get_from_log(file)

        self.assertEqual(len(dates), 3496, "Should read 3496 DATES")
        self.assertEqual(
            dat_dates.to_str(dates[0]),
            '2018 09 03',
            "First date is not correct")
        self.assertEqual(
            dat_dates.to_str(dates[-1]),
            '2049 01 01',
            "Last date is not correct")


    def test_get_progress(self):
        """Check reading simulation progress"""

        folder = Path('tests/_no_sync/ex/dat/')
        file = folder / 'base_case_bo.dat'
        dates = dat_dates.get_from_dat(file)

        progress = dat_dates.get_progress(dates, dates[0])
        self.assertEqual(progress, 0, "Should be 0%")
        progress = dat_dates.get_progress(dates, dates[-1])
        self.assertEqual(progress, 1, "Should be 100%")

        new_date = dates[0] + (dates[-1] - dates[0])/4
        progress = dat_dates.get_progress(dates, new_date)
        self.assertEqual(progress, 0.25, "Should be 25%")


    def test_read_wells(self):
        """Check reading wells in dat file"""

        folder = Path('tests/_no_sync/ex/dat/')
        file = folder / 'base_case_bo.dat'

        parser = dat_parser.DatParser(ignore=['GRID_keys', 'VFP_keys', 'FLUID_keys'])
        parser.process(file)
        data_ = parser.get()

        wells = dat_run.get_wells(data_, keep_only_first=True, verbose=True)

        self.assertEqual(len(wells), 26, "Should read 26 WELLS")
        self.assertEqual(
            dat_dates.to_str(wells[0][0]),
            '2018 09 02',
            "First date is not correct")
        self.assertEqual(
            wells[0][1],
            'P11',
            "First well is not correct")


    def test_read_well_key(self):
        """Check reading well BHPDEPTH in dat file"""

        folder = Path('tests/_no_sync/ex/dat/')
        file = folder / 'base_case_bo.dat'

        parser = dat_parser.DatParser(ignore=['GRID_keys', 'VFP_keys', 'FLUID_keys'])
        parser.process(file)
        data_ = parser.get()

        wells_ = dat_run.get_well_key(data_, keyword='BHPDEPTH', verbose=True)
        self.assertEqual(len(wells_), 2*26-6, f"Should read {2*26-6} entries")
        p11_values = [w[2] for w in wells_ if w[1] == 'P11']
        self.assertEqual(len(p11_values), 2, "Should read 2 values for P11")
        self.assertEqual(
            p11_values[0],
            5400.0,
            "First value for P11 is not correct")
        self.assertEqual(
            p11_values[1],
            5400.01,
            "Second value for P11 is not correct")

    def test_add_dates(self):
        """Check adding dates to a schedule file"""
        file_path = Path('../SimModels/Unisim_iv_2024/hist/Schedule_history_2024_mod.hist')
        output_path = Path('../SimModels/Unisim_iv_2024/hist/Schedule_history_2024_mod_alt.hist')
        sch_to_daily.process(file_path, output_path, delta_days=5, encoding='utf-8')

        self.assertTrue(output_path.is_file(), "Output file was not created")

        file_path = Path('../SimModels/Unisim_iv_2024/hist/Schedule_history_2024_mod_alt.hist')
        output_path = Path('../SimModels/Unisim_iv_2024/hist/Schedule_history_2024_mod_alt2.hist')
        sch_to_daily.process(file_path, output_path, delta_days=5, encoding='utf-8')

        with open(file_path, 'r', encoding='utf-8') as f1:
            with open(output_path, 'r', encoding='utf-8') as f2:
                self.assertEqual(f1.read(), f2.read(), "The files do not have the same content")

        os.remove(file_path)
        os.remove(output_path)

    def test_read_pvt(self):
        """Check reading PVT data in dat file"""
        path = '../SimModels/Unisim_iv_2024/dat_bo/base_case_bo.dat'
        pvt = dat_pvt.get_from_dat(path, verbose=False)

        self.assertEqual(len(pvt), 1, "Should read 1 PVT table")

        data = np.array([
            [152.7532, 270],  #Saturated, has undersaturated
            [152.7532, 450],  #Undersaturated, has undersaturated
            [275.5254, 450],  #Saturated, no undersaturated
            [275.5254, 510],  #Undersaturated, no undersaturated
        ])
        interp_ = dat_pvt.get_pvt_values(pvt[0], data, check_psat=True)

        true_ = {
            'RS': [152.7532, 152.7532, 275.5254, 275.5254,],
            'PRES': [270, 450, 450, 510],
            'PSAT': [270, 270, 450, 450],
            'PNORM': [0.0, 0.642857143, 0.0, 0.6],
            'BO': [1.3877, 1.3595, 1.6554, 999.999],
            'BG': [0.00373 , 0.00288, 0.00288, 0.00275],
            'EG': [1/0.00373 , 1/0.00288, 1/0.00288, 1/0.00275],
            'UO': [1.4887, 1.8318, 0.9242, 999.999],
            'UG': [0.03638, 0.06156, 0.06156, 0.07026],
        }

        for key, values in true_.items():
            for i, val in enumerate(values):
                if val == 999.999:
                    continue
                self.assertAlmostEqual(
                    interp_[key][i],
                    val,
                    msg=f"{i+1}th value for {key} is not correct",
                    places=4
                )


if __name__ == '__main__':
    unittest.main()
