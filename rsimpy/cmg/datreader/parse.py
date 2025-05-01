"""Module to parse CMG dat files."""
import re
import json
from pathlib import Path


SECTION_keys = ['TITLE1','GRID','ROCKFLUID','INITIAL','NUMERICAL','RUN']
GRID_keys = ['CORNERS','COORD','ZCORN','TRANSF','NULL','PINCHOUTARRAY',
             'POR','NETGROSS','PERMI','PERMJ','PERMK',
             'RTYPE','EOSTYPE','ITYPE','PTYPE']
KREL_keys = ['RPT']
FLUID_keys = ['MODEL']
VFP_keys = ['PTUBE1','ITUBE1','VFPPROD','VFPINJ']
WELL_keys = ['WELL','PERF','LAYERCLUMP','PERF','LAYERXYZ']
TRIGGER_keys = ['TRIGGER','END_TRIGGER']
ENCODINGS = ['utf-8', 'cp1252', 'iso8859_2', 'ascii',
             'utf_7','utf_16','utf_32', 'ISO-8859-1', 'windows-1252']


# MARK: DatParser
class DatParser:

    """
    Class with code to read keywords in a CMG simulation file.

    Attributes
    ----------
    abs_path : dict
        Dictionary with changes to absolute pathes. Keys are the
        strings to be searched in the start of the include path,
        and values are the strings to replace any positive search.
        If None, no search is performed. Default: None.
    encoding : str
        File encoding. Default: 'utf-8'.
    ignore : str or [str]
        List of keywords to ignore. Available collections of
        keywords: GRID_keys, VFP_keys, WELL_keys, TRIGGER_keys.
        To use, enter collections names as strings in the list.
        If a section keyword is used, all keywords in the section are ignored.
        Section keywords are: TITLE1, GRID, ROCKFLUID, INITIAL,
        NUMERICAL, RUN. If None, reads all keywords. Default: None.
    verbose : bool
        Print messages. Default: False.

    Methods
    -------
    process(file_path, read_includes=True):
        Process dat file.
    get():
        Return list of keywords and associated options.
    save(file_path):
        Save keywords and options to json file.
    """


    def __init__(self, abs_path=None, encoding='utf-8', ignore=None, verbose=False, _debug=False):
        if abs_path is None:
            self._abs_path = {}
        else:
            self._abs_path = abs_path
        self._encoding = encoding
        self._ignore = DatParser._process_ignore(ignore)
        if verbose:
            print(f'Keywords to ignore: {", ".join(self._ignore)}')
        self._verbose = verbose
        self._debug = _debug

        self._file_path = None
        self._result = []


    @staticmethod
    def _process_ignore(ignore):
        """Process ignore list."""
        if ignore is None:
            return []

        if isinstance(ignore, str):
            ignore = [ignore]

        if isinstance(ignore, list):
            output = []
            for s in ignore:
                if s == 'GRID_keys':
                    output += GRID_keys
                elif s == 'VFP_keys':
                    output += VFP_keys
                elif s == 'WELL_keys':
                    output += WELL_keys
                elif s == 'TRIGGER_keys':
                    output += TRIGGER_keys
                elif s in TRIGGER_keys:
                    output += TRIGGER_keys
                else:
                    output.append(s)
            return list(set(output))

        msg = 'Argument ignore must be a string or a list of strings.'
        raise ValueError(msg)


    def get(self):
        """Return dict of keywords and associated options."""
        return self._result


    # MARK: Save & Load
    def save(self, file_path):
        """Save keywords and options to json file."""
        if self._file_path is None:
            msg = 'No file processed.'
            raise ValueError(msg)

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path = file_path.with_suffix('.json')
        if self._verbose:
            print(f'Saving {file_path.resolve().absolute()}.')
        if file_path.is_file():
            print(f'File already exists: {file_path}.')
            answer = 'y'
            while answer.lower() not in ['y','']:
                print('Overwrite? ([y]/n)')
                answer = input()
                if answer.lower() == 'n':
                    return

        i=1
        result = {}
        for key in self._result:
            result[f'{i}. {key[0]}'] = key[1:]
            i += 1
        with open(file_path, 'w', encoding=self._encoding) as file:
            json.dump(result, file, indent=4)


    def load(self, file_path):
        """Load keywords and options from json file."""
        file_path = Path(file_path)
        if not file_path.is_file():
            msg = f'File not found: {file_path}.'
            raise ValueError(msg)

        with open(file_path, 'r', encoding=self._encoding) as file:
            result = json.load(file)
        self._result = []
        for key, value in result.items():
            key = key.split('. ')[1:]
            self._result.append(key + value)

        if self._verbose:
            print(f'Loaded {file_path.resolve().absolute()}.')


    # MARK: Process
    def process(self, file_path, read_includes=True):
        """Process dat file."""
        self._file_path = None

        if self._verbose:
            print(f'Processing {file_path}.')

        file_path = Path(file_path)
        if not file_path.is_file():
            msg = f'File not found: {file_path}.'
            raise ValueError(msg)

        self._file_path = file_path
        self._result = []

        if self._verbose:
            print('Reading main dat file.')
        txt = self._get_txt(file_path=file_path)

        if self._verbose:
            print('Processing main dat file.')
        self._search_keywords(
            txt=txt,
            is_include=not read_includes,
        )


    # MARK: Read
    def _get_txt(self, file_path, keyword=None):
        """Read file and return code after given keyword."""

        txt = self._safe_file_read(file_path)
        txt = DatParser._clean_line(
            txt=txt,
            multilines=True,
            remove_triggers='TRIGGER' in self._ignore)

        if keyword is None:
            return txt.split('\n')

        txt = f'\n{txt}\n'
        if f'\n{keyword}\n' not in txt:
            msg = f'{keyword} not found in file.'
            raise ValueError(msg)

        txt = txt.split(f'\n{keyword}\n')[1:]
        if len(txt) > 1:
            msg = f'{keyword} found more than once.'
            raise ValueError(msg)

        return txt[0].split('\n')


    def _safe_file_read(self, file_path):
        """Changes file enconding if initial file read fails."""
        try:
            with open(file_path, 'r', encoding=self._encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            if self._verbose:
                print(f'Error reading: {file_path.name}. Trying different encoding.')
            for encoding in [e for e in ENCODINGS if e != self._encoding]:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        txt = file.read()
                    self._encoding = encoding
                    if self._verbose:
                        print(f'Changed encoding to {self._encoding}.')
                    return txt
                except: #pylint: disable=bare-except
                    pass
        raise UnicodeEncodeError('Could not open file.')


    # MARK: Helpers
    @staticmethod
    def _clean_line(txt, multilines=False, remove_triggers=True):
        sub = {
            'comments': (r'\*\*.*$', ''),
            'tabs': (r'\t{1,}', ' '),
            'keyword asterisks': (r'(\s)\*(\w)', r"\g<1>\g<2>"),
            'initial spaces': (r'^\s+',''),
            'final spaces': (r'\s+$',''),
            'double blank lines': (r'^\n\n', '\n'),
        }

        if multilines:
            flag = re.MULTILINE
        else:
            flag = 0

        for (search_,replace_) in sub.values():
            txt = re.sub(search_, replace_, txt, flags=flag)
        txt = txt.lstrip(r'\*')

        if multilines and remove_triggers:
            txt = DatParser._remove_triggers(txt)

        return txt


    @staticmethod
    def _remove_triggers(lines):
        while True:
            start_index = lines.rfind('\nTRIGGER')
            end_index = lines.find('\nEND_TRIGGER', start_index)
            if start_index == -1 or end_index == -1:
                return lines
            lines = lines[:start_index] + lines[end_index + len('\nEND_TRIGGER'):]


    @staticmethod
    def _is_float(value):
        try:
            float(value)
            return True
        except ValueError:
            return False


    @staticmethod
    def _get_key(line):
        if len(line) == 0 or line[0]=="'" or line[:3]=="BG ":
            return None
        split_line = line.split()
        if '*' in split_line[0] or ':' in split_line[0]:
            return None
        if DatParser._is_float(split_line[0]):
            return None
        return split_line[0]


    @staticmethod
    def _get_key_values(line, key=None):
        """Split a string by spaces, ignoring spaces within quotes."""
        if key is not None:
            if line.startswith(key):
                line = line[len(key):]
            else:
                raise ValueError(f'Expected {key} in line: {line}')

        return re.findall(r'(?:[^\s"\']|"(?:\\.|[^"])*"|\'(?:\\.|[^\'])*\')+', line)


    def _resolve_relative_path(self, relative_path):
        relative_path = relative_path.replace('\\', '/')
        for k,v in self._abs_path.items():
            if relative_path.startswith(k):
                path_ = re.sub(f'^{k}', v, relative_path)
                return Path(path_)
        path_ = self._file_path.parent / relative_path
        return path_.resolve()


    # MARK: Search Keywords
    def _search_keywords(self, txt, is_include=True):
        check_first_key = is_include
        current_key = ''
        for line in txt:
            if line == '':
                continue
            new_key = DatParser._get_key(line)
            options = DatParser._get_key_values(line, new_key)
            if new_key is None:
                if current_key not in self._ignore:
                    self._result[-1].extend(options)
                continue

            if new_key in self._ignore:
                current_key = new_key
                self._result.append([new_key])
                self._result[-1].append('ignored')
                if check_first_key:
                    if self._verbose:
                        print(f'  Found {new_key} => stop reading include file.')
                    return True
                check_first_key = False
                continue

            if new_key == 'INCLUDE':
                if current_key in self._ignore:
                    if self._verbose:
                        print(f'  Found {current_key} before INCLUDE => prevent reading include file.')
                    self._result.append([new_key])
                    self._result[-1].extend(options)
                    self._result[-1].append('ignored')
                    continue
                if self._verbose:
                    include_name = options[0][1:-1].replace('\\','/').split('/')[-1]
                    print(f'  Reading include file: {include_name}.')

                include_path = self._resolve_relative_path(options[0][1:-1])
                if not include_path.is_file():
                    print(f'  File not found: {include_path}')
                    self._result.append([new_key])
                    self._result[-1].extend(options)
                    self._result[-1].append('file not found')
                    continue

                include_txt = self._get_txt(file_path=include_path)
                if not self._search_keywords(include_txt, is_include=True):
                    print(f'Error reading include file: {include_path}')
                    return False

            else:
                current_key = new_key
                self._result.append([new_key])
                self._result[-1].extend(options)

            if current_key == 'STOP':
                if self._verbose:
                    print('Found STOP.')
                return False
        return True



if __name__ == "__main__":
    print(__doc__)
    print(DatParser.__doc__)

    dat_parser = DatParser(
        encoding='utf-8',
        ignore=['TITLE1', 'GRID_keys', 'VFP_keys', 'WELL_keys',
                'FLUID_keys', 'TRIGGER_keys', 'KREL_keys'],
        verbose=True,
    )
    dat_parser.process('tests/_no_sync/ex/dat/base_case_bo.dat')
    dat_parser.save('tests/_no_sync/ex/dat/base_case_bo.json')
