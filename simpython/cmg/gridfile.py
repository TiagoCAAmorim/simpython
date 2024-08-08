"""
Implements class GridFile
"""
from pathlib import Path
import numpy as np


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
    def read():
        Reads the contents of the grid file.
    write(file_path=None, coord_range=None, keyword=None, comments=None):
        Writes grid file.
    rewrite_all_grid_files(folder_path=None, new_suffix=None, verbose=False):
        Rewrites all grid files found in folder.

    set_file_path(file_path):
        Sets path to grid file.
    get_file_path():
        Gets path to grid file.
    set_max_line_size(max_line_size):
        Sets maximum number of characters in a line.
    get_max_line_size():
        Gets maximum allowed number of characters in a line.
    set_comments(comments):
        Sets comments to be writen on file.
    get_comments():
        Gets comments.
    set_keyword(keyword):
        Sets the keyword line to be writen on file.
    get_keyword():
        Gets the keyword line.
    set_values(values):
        Sets values by cell.
    get_values(flattened=True, coord_range=None):
        Gets values by cell.
    get_number_values():
        Returns the number of values found in the grid file.
    set_shape(shape):
        Sets the number of cells in each direction.
    set_encoding(encoding):
        Sets encoding used for reading and writting files.

    n2ijk(n):
        Returns (i,j,k) coordinates of the n-th cell.
    ijk2n(i, j=None, k=None):
        Returns cell number of the (i,j,k) cell.
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
                      'values': np.empty(1)}
        self.shape = None
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
        """Gets the keyword line."""
        return self._data['keyword']

    def n2ijk(self, n):
        """Returns (i,j,k) coordinates of the n-th cell.

            Parameters
            ----------
            n : int
                Cell number, from 1 to number of values.

            Raises
            ------
            ValueError
                If an incorrect cell number is provided.
            ValueError
                If shape is not defined.
        """
        if n < 1:
            msg = "Cells number must be greater than or equal to 1."
            raise ValueError(msg)

        if self.shape is None:
            msg = "Grid size is not defined."
            raise ValueError(msg)
        ni, nj, nk = self.shape

        if n > ni*nj*nk:
            msg = "Cells number must be smaller than or equal to number of values."
            raise ValueError(msg)

        k = int(n/(ni*nj)) + 1
        j = int( (n/ni - (k-1)*nj)) + 1
        i = n - (k-1)*ni*nj - (j-1)*ni + 1
        return i, j, k

    def ijk2n(self, i, j=None, k=None):
        """Returns cell number of the (i,j,k) cell.

            Parameters
            ----------
            i : int or list/tuple
                i direction coordinate or list/tuple
                with (i,j,k) coordinates.
            j : int, optional
                j direction coordinate. Assumes i contains
                all coordinates if None is provided.
                (default: None)
            k : int, optional
                k direction coordinate. Assumes i contains
                all coordinates if None is provided.
                (default: None)

            Raises
            ------
            ValueError
                If an incorrect coordinate is provided.
            ValueError
                If shape is not defined.
        """
        if (j is None) and (k is None):
            if len(i) != 3:
                msg = f"Expected 3 coordinates, found {len(i)}."
                raise ValueError(msg)
            i, j, k = i
        if (j is not None) and (k is None):
            msg = "Coordinates must be provided as a tuple/list or separate arguments."
            raise ValueError(msg)
        if (j is None) and (k is not None):
            msg = "Coordinates must be provided as a tuple/list or separate arguments."
            raise ValueError(msg)

        if (i < 1) or (j < 1) or (k < 1):
            msg = "Coordinates number must be greater than or equal to 1."
            raise ValueError(msg)

        if self.shape is None:
            msg = "Grid size is not defined."
            raise ValueError(msg)
        ni, nj, nk = self.shape

        if (i > ni) or (j > nj) or (k > nk):
            msg = "Coordinates number must be smaller than or equal to grid sizes."
            raise ValueError(msg)

        return (k - 1)*ni*nj + (j - 1)*ni + i - 1


    def set_values(self, values):
        """Sets values by cell."""
        self._data['values'] = np.array(values).flatten()


    def get_values(self, flattened=True, coord_range=None):
        """Gets values by cell.

            Parameters
            ----------
            flattened : bool, optional
                Shape of the return ndarrray.
                (default: True)
            coord_range : tuple of 2-element tuples, optional
                Coordinates ranges of a subgrid. Expected
                format: ((i1, i2), (j1,j2), (k1,k2))
                If None is provided the full grid is returned
                (default: None)

            Raises
            ------
            ValueError
                If incorrect ranges are provided.
        """

        values = self._data['values']
        if coord_range is not None:
            if self.shape is None:
                msg = "Grid shape not defined."
                raise ValueError(msg)

            (i1, i2), (j1, j2), (k1, k2) = coord_range
            if (i1 < 1) or (j1 < 1) or (k1 < 1):
                msg = "All coordinates must be positive."
                raise ValueError(msg)

            if (i1 > i2) or (j1 > j2) or (k1 > k2):
                msg = "First coordinate must be smaller than or equal to second."
                raise ValueError(msg)

            ni, nj, nk = self.shape
            if (i2 > ni) or (j2 > nj) or (k2 > nk):
                msg = "Coordinates must be smaller than grid size."
                raise ValueError(msg)

            values = values.reshape((nk, nj, -1))
            values = values[k1-1:k2, j1-1:j2, i1-1:i2]
            nj = j2 - j1 + 1
            nk = k2 - k1 + 1

        if flattened:
            return values.flatten()
        return values.reshape((nk, nj, -1))


    def get_number_values(self):
        """Returns the number of values found in the grid file."""
        if len(self._data['values']) == 0:
            self.read()
        return len(self._data['values'])


    def set_shape(self, shape):
        """Sets the number of cells in each direction.

            Parameters
            ----------
            Shape : list or tuple
                Three values are expected: [ni, nj, nk]

            Raises
            ------
            ValueError
                If number of shape values does not equal 3.
            ValueError
                If product of shape values does not equal
                number of cell values.
        """
        if len(shape) != 3:
            msg = f"Expected 3 values, found {len(shape)}."
            raise ValueError(msg)
        n = self.get_number_values()
        ni, nj, nk = shape
        if n != ni*nj*nk:
            msg = "Shape values do not equal number of values: "
            msg += f"expected {n}, found {ni*nj*nk}."
            raise ValueError(msg)
        self.shape = shape


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
        data['values'] = np.array(data['values'])
        self._data = data
        if self.shape is not None:
            ni, nj, nk = self.shape
            if ni*nj*nk != len(data['values']):
                self.shape = None


    @staticmethod
    def _write(output_file_path, values, keyword, comments, encoding='utf-8', max_line_size=80):
        """Writes grid file.

            Parameters
            ----------
            output_file_path: str
                Path to output file
            values: list of float/int
                list of values
            keyword: list of str
                associated keyword
            comments: list of str
                associated comments

            Raises
            ------
            ValueError
                If an invalid path is provided.
        """

        lines = [comments]
        lines.append(keyword)

        current_line = ''

        def add_line(s, current_line):
            if len(current_line) + len(s) > max_line_size:
                lines.append(current_line)
                current_line = ''
            return current_line + s

        current_value = 0
        n_values = 0
        for value in values:
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
            output_file_path.write_text(content, encoding=encoding)
        except (ValueError, TypeError, NameError) as e:
            msg = 'Could not write file: '
            msg += output_file_path
            raise ValueError(msg) from e


    def write(self, file_path=None, coord_range=None,
              keyword=None, comments=None):
        """Writes grid file.

            Parameters
            ----------
            file_path: str, optional
                Path to output file. If None is provided the
                objects' file_path is used.
                (default: None)
            coord_range : tuple of 2-element tuples, optional
                Coordinates ranges of a subgrid. Expected
                format: ((i1, i2), (j1,j2), (k1,k2))
                If None is provided the full grid is returned
                (default: None)
            keyword : str, optional
                Keyword to be used. If None is provided the
                original keyword is used.
                (default: None)
            comments : list of str, optional
                Comments to be used. If None is provided the
                original comments are used.
                (default: None)

            Raises
            ------
            ValueError
                If an invalid path is provided.
        """
        if file_path is None:
            file_path = self._file_path
        else:
            file_path = Path(file_path)

        if coord_range is None:
            values = self._data['values']
        else:
            values = self.get_values(coord_range=coord_range)

        if keyword is None:
            keyword = self._data['keyword']
        if comments is None:
            comments = self._data['comments']

        GridFile._write(
            output_file_path=file_path,
            values=values,
            keyword=keyword,
            comments=comments,
            encoding=self._encoding,
            max_line_size=self._max_line_size)


    def rewrite_all_grid_files(self, folder_path=None, new_suffix=None, verbose=False):
        """Rewrites all grid files found in folder.

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
                    msg = 'Could not rewrite file: '
                    msg += out_file_path
                    raise ValueError(msg) from e
