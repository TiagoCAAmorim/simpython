"""
Implements class GridFile
"""
from pathlib import Path


class GridFile:

    """
    Class that represents a grid file

    ...

    Attributes
    ----------
    file_path : str
        Path to template file.
    max_line_size : int
        Maximum number of characters in a line (default: 80)
    comments: str
        Comments associated to the grid file
    keyword: str
        Keyword associated to the grid file
    values : list
        Values by cell.
    number_values : int
        Number of values found in the grid file.
    encoding : str
        Encoding used for reading and writting files (default: 'utf-8')

    Methods
    -------
    read():
        Reads the contents of the grid file.
    write(output_file_path):
        Writes data into a grid file.
    """

    def __init__(self, file_path, encoding='utf-8', auto_read=True):
        """
        Parameters
        ----------
        file_path : str
            Path to grid file.
        encoding : str, optional
            Encoding used for reading and writting files.
            (default: 'utf-8')
        auto_read : bool, optional
            Defines if should try to read input file.
            (default: True)
        """

        self._file_path = Path(file_path)
        self._max_line_size = 80
        self._data = {'keyword': '',
                      'comments': [],
                      'values': []}
        self._encoding = encoding
        if auto_read and self._file_path.exists():
            if self._file_path.is_file():
                self.read()

    def set_file_path(self, file_path):
        """Sets path to grid file.

        Parameters
        ----------
        file_path : str
            Path to the grid file.
        """
        self._file_path = Path(file_path)

    def get_file_path(self):
        """Gets path to grid file."""
        return str(self._file_path)

    def set_max_line_size(self, max_line_size):
        """Sets maximum number of characters in a line.

        Parameters
        ----------
        max_line_size : int
            Maximum number of characters in a line.
        """
        self._max_line_size = int(max_line_size)

    def get_max_line_size(self):
        """Gets maximum allowed number of characters in a line."""
        return self._max_line_size

    def set_comments(self, comments):
        """Sets comments to be writen on file.

        Parameters
        ----------
        comments : str or [str]
            Comments to be written on file.
        """
        if isinstance(comments, str):
            comments = comments.split('\n')
        for i, v in enumerate(comments):
            if len(v) < 2:
                comments[i] = ' '.join(['**', v])
            elif not v.strip().startswith('**'):
                comments[i] = ' '.join(['**', v])
        self._data['comments'] = comments

    def get_comments(self):
        """Gets comments."""
        return '\n'.join(self._data['comments'])

    def set_keyword(self, keyword):
        """Sets the keyword line to be writen on file.

        Parameters
        ----------
        keyword : str
            Keyword line to be written on file.
        """
        self._data['keyword'] = keyword

    def get_keyword(self):
        """Gets the keyword line"""
        return self._data['keyword']

    def set_values(self, values):
        """Sets list of values by cell."""
        self._data['values'] = values

    def get_values(self):
        """Gets list of values by cell."""
        return self._data['values']

    def get_number_values(self):
        """Returns the number of values found in the grid file."""
        if len(self._data['values']) == 0:
            self.read()
        return len(self._data['values'])

    def set_encoding(self, encoding):
        """Sets encoding used for reading and writting files.

        Parameters
        ----------
        encoding : str
            File encoding to be used.
        """
        self._encoding = encoding

    def read(self):
        """Reads the contents of the grid file.

            Parameters
            ----------
            None

            Raises
            ------
            ValueError
                If an invalid path is provided.
            ValueError
                If the file contains data that is not numeric.
        """
        data = {'keyword': '', 'comments': [], 'values': []}

        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False

        def int_or_float(s):
            try:
                x = int(s)
                return x
            except ValueError:
                try:
                    x = float(s)
                    return x
                except (ValueError, TypeError, NameError) as e:
                    msg = "Input string is not a valid number"
                    raise ValueError(msg) from e

        def is_line_with_values(line):
            parts = line.split(' ')
            parts = parts[0].split('*')
            return is_number(parts[0])

        if not self._file_path.exists():
            raise FileNotFoundError(
                f"Grid file '{self._file_path}' not found.")
        if not self._file_path.is_file():
            raise FileNotFoundError(
                f"Provided path is not a file: {self._file_path}.")


        with self._file_path.open(mode='r', encoding=self._encoding) as file:
            for line in file:
                line = line.strip()
                if line == '':
                    pass
                elif line.strip().startswith('**'):
                    data['comments'].append(line)
                elif not is_line_with_values(line):
                    if data['keyword'] != '':
                        raise ValueError("More than one keyword line found!")
                    data['keyword'] = line
                else:
                    parts = line.split('**')
                    parts = parts[0].strip().split(' ')
                    for n in parts:
                        value = n.split('*')
                        if len(value) == 1:
                            data['values'].append(int_or_float(value[0]))
                        else:
                            data['values'].extend(
                                [int_or_float(value[1]) for _ in range(int_or_float(value[0]))])

        if len(data['values']) == 0:
            raise ValueError("Input file is not a grid file!")
        self._data = data

    def write(self, output_file_path=None):
        """Writes grid file.

            Parameters
            ----------
            output_file_path: str, optional
                Path to output file
                (default: file_path)

            Raises
            ------
            ValueError
                If an invalid path is provided.
        """
        if output_file_path is None:
            output_file_path = self._file_path
        else:
            output_file_path = Path(output_file_path)

        lines = self._data['comments'].copy()
        lines.append(self._data['keyword'])

        current_line = ''

        def add_line(s, current_line):
            if len(current_line) + len(s) > self._max_line_size:
                lines.append(current_line)
                current_line = ''
            return current_line + s

        current_value = 0
        n_values = 0
        for value in self._data['values']:
            if value == current_value:
                n_values += 1
            else:
                if n_values == 1:
                    current_line = add_line(
                        s=' '+str(current_value), current_line=current_line)
                elif n_values > 1:
                    current_line = add_line(
                        s=' '+str(n_values)+'*'+str(current_value), current_line=current_line)
                current_value = value
                n_values = 1

        if n_values == 1:
            lines.append(current_line+' '+str(current_value))
        elif n_values > 1:
            lines.append(current_line+' '+str(n_values)+'*'+str(current_value))

        content = '\n'.join(lines)
        try:
            output_file_path.write_text(content, encoding=self._encoding)
        except (ValueError, TypeError, NameError) as e:
            msg = f'Could not write file: {
                output_file_path}'
            raise ValueError(msg) from e

    def rewrite_all_grid_files(self, folder_path=None, new_suffix=None, verbose=False):
        """Rewrites all grid file found in folder.

            Parameters
            ----------
            folder_path: str, optional
                Path to output file
                (default: file_path parent folder)
            new_suffix: str, optional
                New suffix for grid files
                (default: same as original file)
            verbose: bool, optional
                Print additional info
                (default: False)

            Raises
            ------
            ValueError
                If fails to write grid file.
        """
        if folder_path is None:
            folder_path = self._file_path.parent

        if folder_path.is_dir():
            for file in folder_path.iterdir():
                if file.is_file():
                    self.rewrite_all_grid_files(folder_path=file,
                                                new_suffix=new_suffix,
                                                verbose=verbose)
        else:
            file_path = folder_path
            if verbose:
                print(f'Reading {file_path.name}...')
            try:
                grid_file = GridFile(file_path=file_path,
                                     encoding=self._encoding, auto_read=True)
                ok = True
            except ValueError:
                print(f'{file_path.name} is not a valid grid file.')
                ok = False
            if ok:
                if new_suffix is None:
                    out_file_path = file_path
                else:
                    out_file_path = file_path.with_suffix(new_suffix)
                if verbose:
                    print(f'Exporting {out_file_path.name}...')
                try:
                    grid_file.write(out_file_path)
                except ValueError as e:
                    msg = f'Could not rewrite file: {
                        out_file_path}'
                    raise ValueError(msg) from e
