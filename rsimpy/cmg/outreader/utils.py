"""
Module with utility functions for reading CMG output files.

Functions
--------
get_file_type(file_path, encoding='utf-8'):
    Determine the type of CMG output file based on its content.
"""

def get_file_type(file_path, encoding='utf-8'):
    """
    Determine the type of CMG output file based on its content.

    Args:
        file_path (str): Path to the CMG output file.
        encoding (str): Encoding of the file. Default is 'utf-8'.
    Returns:
        str: Type of the CMG output file ('IMEX' or 'GEM').
    Raises:
        ValueError: If the file type cannot be determined.
    """
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            found_header = False
            for line in file:
                trimmed_line = line.strip()
                if trimmed_line.startswith('*'):
                    found_header = True
                    trimmed_line = trimmed_line[1:].strip()
                    if trimmed_line.startswith('IMEX '):
                        return 'IMEX'
                    if trimmed_line.startswith('GEM '):
                        return 'GEM'
                elif found_header:
                    raise ValueError('Could not identify file type!')
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {file_path}") from e
    raise ValueError('Could not identify file type!')

if __name__ == "__main__":
    print(__doc__)
