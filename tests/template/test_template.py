from simpython import template
from pathlib import Path
import tempfile
import matplotlib.pyplot as plt


def process_temporary_file(text, verbose=False, variables_df=None, output_file_path=None, all_uniform=False, n_samples=0):
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(text)
            temp_file_path = Path(temp_file.name)

        temp_csv_file_path = None
        if variables_df is not None:
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_csv_file:
                variables_df.to_csv(temp_csv_file.name, index=False)
                temp_csv_file_path = Path(temp_csv_file.name)
        
        return template.TemplateProcessor(template_path=temp_file_path, verbose=verbose, variables_table_path=temp_csv_file_path, output_file_path=output_file_path, all_uniform=all_uniform, n_samples=n_samples)       

    finally:
        temp_file_path.unlink()
        if variables_df is not None:
            temp_csv_file_path.unlink()


def plot_histogram(data, bins=30, title='Histogram of Data'):
    plt.figure(figsize=(4, 2))
    plt.hist(data, bins=bins, density=True, alpha=0.75)
    plt.title(title)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.show()            