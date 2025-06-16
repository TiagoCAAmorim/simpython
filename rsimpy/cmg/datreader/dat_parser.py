"""Module to parse CMG dat files."""
import re
import json
from pathlib import Path

try:
    from rsimpy.cmg.datreader.dat_common import safe_file_read, safe_file_read_by_line
except ImportError:
    from dat_common import safe_file_read, safe_file_read_by_line

# MARK: Constants
SECTION_keys = ['TITLE1','GRID','ROCKFLUID','INITIAL','NUMERICAL','RUN']
IGNORE_keys = {
    'GRID_keys': ['CORNERS','COORD','ZCORN','TRANSF','NULL','PINCHOUTARRAY',
                'POR','NETGROSS','PERMI','PERMJ','PERMK',
                'RTYPE','EOSTYPE','ITYPE','PTYPE'],
    'KREL_keys': ['RPT'],
    'FLUID_keys': ['MODEL'],
    'VFP_keys': ['PTUBE1','ITUBE1','VFPPROD','VFPINJ'],
    'WELL_keys': ['LAYERCLUMP','PERF','LAYERXYZ'],
    'TRIGGER_keys': ['TRIGGER','END_TRIGGER'],
}


# MARK: DatParser
class DatParser: #pylint: disable=too-many-instance-attributes

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
        self._result = {}
        self._current_section = ''


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
                if s in IGNORE_keys:
                    output += IGNORE_keys[s]
                elif s in IGNORE_keys['TRIGGER_keys']:
                    output += IGNORE_keys['TRIGGER_keys']
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
        if len(self._result) == 0:
            msg = 'No keywords found. Nothing to save.'
            raise ValueError(msg)

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path = file_path.with_suffix('.json')
        if self._verbose:
            print(f'Saving {file_path.resolve().absolute()}.')
        if file_path.is_file():
            print(f'File already exists: {file_path}.')
            answer = 'y' if self._debug else 'n'
            while answer.lower() not in ['y','']:
                print('Overwrite? ([y]/n)')
                answer = input()
                if answer.lower() == 'n':
                    return

        i=1
        result = {}
        for sec_name, section in self._result.items():
            result[sec_name] = {}
            for key in section:
                result[sec_name][f'{i}. {key[0]}'] = key[1:]
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

        self._result = {}
        for sec_name, section in result.items():
            self._result[sec_name] = []
            for key, options in section.items():
                key = key.split('. ')[1:]
                self._result[sec_name].append(key + options)

        if self._verbose:
            print(f'Loaded {file_path.resolve().absolute()}.')


    # MARK: Process
    def process(self, file_path):
        """Process dat file."""
        self._file_path = None

        if self._verbose:
            print(f'Processing {file_path}.')

        file_path = Path(file_path)
        if not file_path.is_file():
            msg = f'File not found: {file_path}.'
            raise ValueError(msg)

        self._file_path = file_path
        if self._verbose:
            print('Reading main dat file.')

        txt = self._safe_file_read(
            file_path=file_path,
            lines_fn=self._clean_lines_wrapper).split('\n')

        self._result = {}
        self._current_section = 'No section'
        if self._verbose:
            print('Processing main dat file.')
        self._search_keywords(txt)


    def _clean_lines_wrapper(self, lines):
        """Wrapper for _clean_line to process lines."""
        return DatParser._clean_line(
            txt=lines,
            multilines=True,
            remove_triggers='TRIGGER' in self._ignore)


    # MARK: Read File
    def _safe_file_read(self, file_path, lines_fn=None):
        """Changes file enconding if initial file read fails."""
        txt = safe_file_read(
            file_path=file_path,
            default=self._encoding,
            verbose=self._verbose)
        if lines_fn is not None:
            txt = lines_fn(txt)
        return txt


    def _read_first_line(self, file_path):
        """
        Read the first line with comands.

        Args:
            file_path (Path): Path to the file.

        Returns:
            tuple: (keyword, [options]) of the first line with commands.
        """

        def _line_fn(line, _):
            line = DatParser._clean_line(line)
            if line == '':
                return (True, (None, None))
            new_key, options = DatParser._get_key_options(line)
            return (None, (new_key, options))

        new_key, options = safe_file_read_by_line(
            file_path, _line_fn, default=self._encoding, verbose=self._verbose)
        return new_key, options


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
    def _get_options(line, key=None):
        """Split a string by spaces, ignoring spaces within quotes."""
        if key is not None:
            if line.startswith(key):
                line = line[len(key):]
            else:
                raise ValueError(f'Expected {key} in line: {line}')

        return re.findall(r'(?:[^\s"\']|"(?:\\.|[^"])*"|\'(?:\\.|[^\'])*\')+', line)


    @staticmethod
    def _get_key_options(line):
        """Return key and options from line."""
        key = DatParser._get_key(line)
        options = DatParser._get_options(line, key=key)
        return key, options


    def _resolve_relative_path(self, relative_path):
        relative_path = relative_path.replace('\\', '/')
        for k,v in self._abs_path.items():
            if relative_path.startswith(k):
                path_ = re.sub(f'^{k}', v, relative_path)
                return Path(path_)
        path_ = self._file_path.parent / relative_path
        return path_.resolve()


    # MARK: Search Keywords
    def _new_key_none(self, current_key, options):
        if current_key not in self._ignore:
            self._result[self._current_section][-1].extend(options)


    def _new_key_in_section(self, new_key):
        if self._verbose:
            print(f'Found section: {new_key}.')
        self._current_section = new_key
        self._result[self._current_section] = []
        if new_key in self._ignore:
            if self._verbose:
                print(f'  Ignoring section: {new_key}.')
            self._result[new_key].append([new_key, '** Ignored section'])
            return False
        return True


    def _add_new_key(self, new_key, options, msg=None):
        self._result[self._current_section].append([new_key])
        self._result[self._current_section][-1].extend(options)
        if msg is not None:
            self._result[self._current_section][-1].append(f'** {msg}')


    def _new_key_include(self, new_key, options, current_key):
        include_path = self._resolve_relative_path(options[0][1:-1])
        if not include_path.is_file():
            print(f'  File not found: {include_path}')
            self._add_new_key(new_key, options, 'File not found')
            return False

        inc_key, inc_options = self._read_first_line(include_path)
        if inc_key is None:
            if inc_options is None:
                if self._verbose:
                    print(f'  No keywords found in include file: {include_path.name}')
                self._add_new_key(new_key, options, 'No data found')
                return False
            if current_key in self._ignore:
                if self._verbose:
                    msg = f'  Found {current_key} before INCLUDE'
                    msg += ' => prevent reading include file.'
                    print(msg)
                self._add_new_key(new_key, options, f'{current_key} before INCLUDE => Ignored')
                return False
        elif inc_key in self._ignore:
            if self._verbose:
                msg = f'  Found {inc_key} in include file: {include_path.name}'
                msg += ' => stop reading include file.'
                print(msg)
            self._add_new_key(new_key, options, f'Found {inc_key} => Ignored')
            return False

        if self._verbose:
            print(f'  Reading include file: {include_path.name}.')
        return True


    def _search_keywords(self, txt): #pylint: disable=too-many-branches
        """Search keywords in text."""
        current_key = ''
        if self._current_section not in self._result:
            self._result[self._current_section] = []

        for line in txt:
            if line == '':
                continue
            new_key, options = DatParser._get_key_options(line)

            if new_key is None:
                self._new_key_none(current_key, options)
                continue

            if new_key in SECTION_keys:
                current_key = new_key
                if not self._new_key_in_section(new_key):
                    continue

            if self._current_section in self._ignore:
                continue

            if new_key in self._ignore:
                current_key = new_key
                self._add_new_key(new_key, options, 'Ignored subsequent options')
                continue

            if new_key == 'INCLUDE':
                if not self._new_key_include(new_key, options, current_key):
                    continue
                include_path = self._resolve_relative_path(options[0][1:-1])
                include_txt = self._safe_file_read(
                    file_path=include_path,
                    lines_fn=self._clean_lines_wrapper).split('\n')
                if not self._search_keywords(include_txt):
                    print(f'Finished reading in include file: {include_path.name}')
                    return False
            else:
                current_key = new_key
                self._add_new_key(new_key, options)

            if current_key == 'STOP':
                if self._verbose:
                    print('Found STOP.')
                return False

        if 'No section' in self._result:
            if self._current_section != 'No section':
                if len(self._result['No section']) == 0:
                    _ = self._result.pop('No section')
        return True


if __name__ == "__main__":
    print(__doc__)
    print(DatParser.__doc__)
