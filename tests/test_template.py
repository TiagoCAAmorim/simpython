"""
template module tests
"""
from pathlib import Path
import tempfile
import shutil
import unittest
import pandas as pd
import numpy as np
from scipy.stats import norm, truncnorm, lognorm, triang  # type: ignore # noqa # pylint: disable=unused-import

import context  # noqa # pylint: disable=unused-import
from rsimpy.common import template


def process_temporary_file(text, verbose=False, variables_df=None,
                           output_file_path=None, all_uniform=False, n_samples=0):
    """Create temp file and run TemplateProcessor initialization"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(text)
            temp_file_path = Path(temp_file.name)

        temp_csv_file_path = None
        if variables_df is not None:
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_csv_file:
                variables_df.to_csv(temp_csv_file.name, index=False)
                temp_csv_file_path = Path(temp_csv_file.name)

        return template.TemplateProcessor(template_path=temp_file_path,
                                          verbose=verbose,
                                          variables_table_path=temp_csv_file_path,
                                          output_file_path=output_file_path,
                                          all_uniform=all_uniform,
                                          n_samples=n_samples)

    finally:
        temp_file_path.unlink()
        if variables_df is not None:
            temp_csv_file_path.unlink()


def delete_temp_folder(temp_dir):
    """Delete the temporary directory and all its contents"""
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


class TestTemplate(unittest.TestCase):
    """Tests template functionalities"""

    def test_no_error(self):
        """Reads and parses a file with 10 variables"""
        text = [
            r"** Some comments",
            r"No variables to read",
            r"The first variable is <\var>var1<var>",
            r"Second is <\var>var2[12]<var> is ok",
            r"<\var>var3[int,42]<var> is an integer",
            r"Now a normal distribution <\var>var4[float,0.5,(normal,0, 2.5)]<var> " +
            "with mean 0 and variance 2.5.",
            r"Another a normal distribution <\var>var5[0.5,(normal,0, 2.5)]<var> " +
            "with mean 0 and variance 2.5.",
            r"just a line",
            r"",
            r"Two variables: <\var>var6[float,7.,(categorical,{1,3,7,-12}" +
            ",{0.2,0.15,0.25,0.400})]<var>",
            r"",
            r"Distribution with explicit type: <\var>var7[(normal,0, 2.5)]<var>",
            r"Distribution with explicit type: <\var>var8[(uniform,0, 12)]<var>",
            r"Distribution with explicit type: <\var>var9[(uniform,0., 12.)]<var>",
            r"Distribution with explicit type: <\var>var10[(constant,0)]<var>",
            r"",
            r"The last line with no variables."
        ]

        templ = process_temporary_file(text='\n'.join(text), verbose=False)

        self.assertEqual(len(templ.variables), 10,
                         "Should read 10 variables")
        self.assertEqual(templ.variables['var1']['distribution'], 'table',
                         "Should be 'table'")
        self.assertEqual(len(templ.variables['var4']['parameters']), 2,
                         "Should be 2")
        self.assertEqual(templ.variables['var8']['type'], 'int',
                         "Should be 'int'")

    def test_import_table(self):
        """Reads a df a saves data into variables"""
        text = [
            r"Variable #1: <\var>var1[17,(table)]<var>.",
            r"Variable #2: <\var>var2<var>.",
            r"Variable #3+4: <\var>var3<var> + <\var>var4<var>.",
            r"Variable #1: <\var>var1<var> & <\var>var1<var>."
        ]

        df = pd.DataFrame()
        df['var1'] = [1, 2, 3, 4]
        df['var2'] = [4, 3, 2, 1]
        df['var3'] = ['a', 'b', 'c', 'd']
        df['var4'] = [10, -20, 300, 404]

        templ = process_temporary_file(text='\n'.join(text),
                                       verbose=False, variables_df=df)
        for k, v in templ.variables.items():
            msg = f"Values in {k} should be equal to df"
            self.assertEqual(v['values'], list(df[k]), msg)

    def test_distributions(self):
        """Checks statistics of distributions"""

        def _truncated_normal_std_dev(mu, sigma, a_trunc, b_trunc):
            a, b = (a_trunc - mu) / sigma, (b_trunc - mu) / sigma
            return truncnorm.std(a, b, loc=0, scale=1)

        distributions_list = {
            'uniform 7-22 discrete': {
                'text': r'<\var>var[int,8,(uniform,7,22)]<var>',
                'min': 7,
                'max': 22,
                'mean': (7 + 22)/2,
                'std_dev': np.sqrt((22-7)*(22-7+2*1)/12)
            },
            'uniform 7-22 continuous': {
                'text': r'<\var>var[float,8,(uniform,7,22)]<var>',
                'min': 7,
                'max': 22,
                'mean': (7 + 22)/2,
                'std_dev': (22-7)/np.sqrt(12)
            },
            'normal 0, 1': {
                'text': r'<\var>var[float,1,(normal,0,1)]<var>',
                'min': -np.inf,
                'max': np.inf,
                'mean': 0,
                'std_dev': 1
            },
            'normal 10, 2': {
                'text': r'<\var>var[float,1,(normal,10,2)]<var>',
                'min': -np.inf,
                'max': np.inf,
                'mean': 10,
                'std_dev': 2
            },
            'truncnormal 0, 1, +-2': {
                'text': r'<\var>var[float,1,(truncnormal,0,1,-2, 2)]<var>',
                'min': -2,
                'max': 2,
                'mean': 0,
                'std_dev': _truncated_normal_std_dev(0, 1, -2, 2)
            },
            'lognormal 0, 1': {
                'text': r'<\var>var[float,1,(lognormal,0,1)]<var>',
                'min': 0,
                'max': np.inf,
                'mean': lognorm.mean(s=1, loc=0, scale=np.exp(0)),
                'std_dev': lognorm.std(s=1, loc=0, scale=np.exp(0))
            },
            'triangular 0,3,1': {
                'text': r'<\var>var[float,1,(triangular,0,3,1)]<var>',
                'min': 0,
                'max': 3,
                'mean': triang.mean(c=1./3, loc=0, scale=3),
                'std_dev': triang.std(c=1./3, loc=0, scale=3)
            },
            'categorical 1/1/2/6': {
                'text': r'<\var>var[int,1,(categorical,{1,2,3,4},{0.1,0.1,0.2,0.6})]<var>',
                'min': 1,
                'max': 4,
                'mean': 3.3,
                'std_dev': 1.004987562112089
            },
        }

        def _aproximate(x1, x2, limit=10**-5):
            if x1 == x2:
                return True
            if x1 == 0 or x2 == 0:
                m = 1
            else:
                m = max(abs(x1), abs(x2))
            return abs(x1-x2)/m < limit

        for k, v in distributions_list.items():
            templ = process_temporary_file(text=v['text'], verbose=False)
            templ.generate_experiments(500)
            data = templ.experiments_table['var']

            self.assertTrue(_aproximate(np.mean(data), v['mean'], 0.05),
                            f"Failed to calculate mean for '{k}': {np.mean(data)} != {v['mean']}")
            self.assertTrue(_aproximate(np.std(data), v['std_dev'], 0.10),
                            f"Failed to calculate std dev for '{k}':" +
                            f" {np.std(data)} != {v['std_dev']}")
            self.assertTrue(np.min(data) >= v['min'],
                            f"Failed to calculate min for '{k}': {np.min(data)} < {v['min']}")
            self.assertTrue(np.max(data) <= v['max'],
                            f"Failed to calculate max for '{k}': {np.max(data)} > {v['max']}")

    def test_generate_files(self):
        """Test file generation based on template"""
        text = [
            r'uniform int         = "<\var>var1[int,1,(uniform,1,10)]<var>"',
            r'uniform float       = "<\var>var2[float,1,(uniform,0,1)]<var>"',
            r'normal 0-1          = "<\var>var3[float,1,(normal,0,1)]<var>"',
            r'normal 10-2         = "<\var>var4[float,1,(normal,10,2)]<var>"',
            r'truncnormal 0-1 +-2 = "<\var>var5[float,1,(truncnormal,0,1,-2, 2)]<var>"',
            r'lognormal 0-1       = "<\var>var6[float,1,(lognormal,0,1)]<var>"',
            r'triangular 0-3-1    = "<\var>var7[float,1,(triangular,0,3,1)]<var>"',
            r'constant int        = "<\var>var8A[int,1,(constant,2)]<var>"',
            r'constant float      = "<\var>var8B[float,1,(constant,2)]<var>"',
            r'constant str        = "<\var>var8C[str,1,(constant,2)]<var>"',
            r'categorical int     = "<\var>var9A[int,1,(categorical,{1,2,3,4}' +
            ',{0.1,0.1,0.2,0.6})]<var>"',
            r'categorical float   = "<\var>var9B[float,1,(categorical,{1,2,3,4}' +
            ',{0.1,0.1,0.2,0.6})]<var>"',
            r'categorical str     = "<\var>var9C[str,1,(categorical,{1,2,3,4}' +
            ',{0.1,0.1,0.2,0.6})]<var>"',
        ]

        n_samples = 10
        temp_dir = Path(tempfile.mkdtemp())
        output_file_path = temp_dir / 'test.dat'
        _ = process_temporary_file(text='\n'.join(text),
                                   verbose=False,
                                   output_file_path=output_file_path,
                                   all_uniform=False,
                                   n_samples=n_samples)

        for k in range(n_samples):
            file_name = f"{output_file_path.stem}_{k}{output_file_path.suffix}"
            msg = f'File {file_name} was not generated.'
            self.assertTrue(Path(temp_dir / file_name).exists(), msg)
        delete_temp_folder(temp_dir=temp_dir)

    def test_error_catching(self):
        """Test error catching"""
        error_list = {
            # 'no error': r'<\var>var[1.5, (normal,0, 2.5)]<var>',
            # 'bogus text 1': r'<\var>var[1.5, (normal,0,2.)ABC]<var>',
            'bogus text 2': r'<\var>var[1.5, (normal,0,2.), ABC]<var>',
            # 'bogus text 3': r'<\var>var[1.5, (normal,0,2.)]ABC<var>',
            # 'bogus text 4': r'<\var>var[1.5, (normal,0,2.)], ABC<var>',
            'too few parameters': r'<\var>var[(normal,0)]<var>',
            'too many parameters': r'<\var>var[(normal,0, 2.5, 7)]<var>',
            'invalid distribution': r'<\var>var[(nomal,0, 2.5)]<var>',
            'missing comma 1': r'<\var>var[float 1.5, (normal,0, 2.5)]<var>',
            'missing comma 2': r'<\var>var[float, 1.5 (normal,0, 2.5)]<var>',
            'missing comma 3': r'<\var>var[float, 1.5, (normal 0, 2.5)]<var>',
            'missing comma 4': r'<\var>var[float, 1.5, (normal,0 2.5)]<var>',
            'type inconsistency': r'<\var>var[str, 1.5, (normal,0, 2.5)]<var>',
            'unclosed var': r'<\var>var[1.5, (normal,0, 2.5)]var>',
        }

        for k, v in error_list.items():
            msg = f'Could not catch the "{k}" error.'
            with self.assertRaises(ValueError, msg=msg):
                _ = process_temporary_file(v)


if __name__ == '__main__':
    unittest.main()
