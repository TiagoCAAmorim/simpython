"""
template module tests
"""
from pathlib import Path
import tempfile
import unittest
import matplotlib.pyplot as plt
import pandas as pd

import context  # noqa
from simpython.common import template


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


def plot_histogram(data, bins=30, title='Histogram of Data'):
    """Plot histogram"""
    plt.figure(figsize=(4, 2))
    plt.hist(data, bins=bins, density=True, alpha=0.75)
    plt.title(title)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.show()


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
            r"Now a normal distribution <\var>var4[float,0.5,(normal,0, 2.5)]<var> "+
             "with mean 0 and variance 2.5.",
            r"Another a normal distribution <\var>var5[0.5,(normal,0, 2.5)]<var> "+
             "with mean 0 and variance 2.5.",
            r"just a line",
            r"",
            r"Two variables: <\var>var6[float,7.,(categorical,{1,3,7,-12}"+
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

        self.assertEqual(len(templ.variables), 10, "Should read 10 variables")
        self.assertEqual(
            templ.variables['var1']['distribution'], 'table', "Should be 'table'")
        self.assertEqual(
            len(templ.variables['var4']['parameters']), 2, "Should be 2")
        self.assertEqual(templ.variables['var8']
                         ['type'], 'int', "Should be 'int'")

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

        templ = process_temporary_file(text='\n'.join(
            text), verbose=False, variables_df=df)
        for k, v in templ.variables.items():
            self.assertEqual(v['values'], list(df[k]), f"Values in {
                             k} should be equal to df")


if __name__ == '__main__':
    unittest.main()
