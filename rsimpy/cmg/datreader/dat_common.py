"""Function common to reading CMG dat files."""

ENCODINGS = ['utf-8', 'cp1252', 'iso8859_2', 'ascii',
             'utf_7','utf_16','utf_32', 'ISO-8859-1', 'windows-1252']


def safe_file_read(file_path, *, default=None, encodings=None, verbose=False):
    """
    Reads a file with different encodings if the first read fails.
    Args:
        file_path (str or Path): Path to the file to read.
        default (str, optional): Default enconding. If None, uses 'utf-8'.
            Default is None.
        encodings (list, optional): List of encodings to try.
            Defaults to None, which uses a predefined list of encodings.
        verbose (bool, optional): If True, print messages about encoding changes.
    Returns:
        str: The content of the file.
    """
    if encodings is None:
        encodings = ENCODINGS
    if default is None:
        default = 'utf-8'
    encodings = [default] + [e for e in encodings if e != default]
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                txt = file.read()
            if verbose and encoding != default:
                print(f'Changed encoding to {encoding}.')
            return txt
        except UnicodeDecodeError:
            if verbose:
                print(f'Error reading: {file_path.name}. Trying different encoding.')
        except FileNotFoundError as e:
            msg = f'File not found: {file_path}.'
            raise ValueError(msg) from e
    raise UnicodeEncodeError('Could not read file.')


def safe_file_read_by_line( # pylint: disable=too-many-arguments
        file_path, line_fn, *, init_result=None,
        default=None, encodings=None, verbose=False):
    """
    Changes file enconding if initial file read by line fails.

    Reads the file line by line and applies the `line_fn` to each line.
    If the file cannot be read with the initial encoding, it tries
    different encodings until it succeeds or raises an error.

    Resumes in the last position if the file is not read completely.

    `line_fn` must return a tuple of two values: (flag, result).
    if flag is None, the function returns the result.
    If the end of the file is reached, the function returns the last result of `line_fn`.

    Args:
        file_path (Path): Path to the file.
        line_fn (function): Function to process each line. It must receive
            the current line and the previous result of a function call
            as arguments and return a tuple of two values: (flag, result).
        init_result (any, optional): Initial result to pass to line_fn,
        default (str, optional): Default enconding. If None, uses 'utf-8'.
            Default is None.
        encodings (list, optional): List of encodings to try.
            Defaults to None, which uses a predefined list of encodings.
        verbose (bool, optional): If True, print messages about encoding changes.
    Returns:
        [str]: The content of the file.
    """
    if encodings is None:
        encodings = ENCODINGS
    if default is None:
        default = 'utf-8'
    encodings = [default] + [e for e in encodings if e != default]

    i_lines = 0
    for encoding in encodings:
        try:
            out = (True, init_result)
            with open(file_path, 'r', encoding=encoding) as file:
                if i_lines > 0:
                    for _ in range(i_lines):
                        file.readline()
                for line in file:
                    out = line_fn(line, out[1])
                    i_lines += 1
                    if isinstance(out, tuple):
                        if out[0] is None:
                            return out[1]
                    else:
                        msg = 'Function must return a tuple of two values.'
                        msg += f' Found {type(out)} instead.'
                        raise ValueError(msg)
                return out[1]
        except UnicodeDecodeError:
            if verbose:
                print(f'Error reading: {file_path.name}. Trying different encoding.')
    raise UnicodeEncodeError('Could not read all file.')


def get_section(data, section, verbose=False):
    """Get data from a specific section in the data read."""
    if section in data:
        return data[section]
    if verbose:
        print(f"No '{section}' section found.")
    if 'No section' in data:
        return data['No section']
    raise ValueError(f"No '{section}' or 'No section' found. Invalid data.")
