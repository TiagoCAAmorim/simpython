"""Module to parse CMG dat files."""
import sys
import re
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
import time
from collections import Counter


VFP_keys = ['PTUBE1','ITUBE1','VFPPROD','VFPINJ']
WELL_keys = ['WELL','PERF','LAYERCLUMP','PERF','LAYERXYZ']
ENCODINGS = ['utf-8', 'cp1252',
             'iso8859_2', 'ascii',
             'utf_7','utf_16','utf_32',
             'ISO-8859-1', 'windows-1252']

# MARK: Timer
class Timer:
    """Helper to time functions."""
    def __init__(self, min_interval=0.0):
        self._min = min_interval
        self._tick = time.time()

    def tick(self):
        """Start stopwatch"""
        self._tick = time.time()

    def tock(self, msg=None):
        """Check elapsed time and print message"""
        elapsed = time.time() - self._tick
        if elapsed > self._min:
            if msg is None:
                msg = 'Elapsed time'
            print(f'{msg}: {elapsed:0.4f} s.')

# MARK: DatDates
class DatDates:

    """
    Class with code to read Dates in a CMG simulation file.

    Attributes
    ----------
    abs_path : dict
        Dictionary with changes to absolute pathes. Default: None.
    encoding : str
        File encoding. Default: 'utf-8'.
    verbose : bool
        Print messages. Default: False.

    Methods
    -------
    process():
        Process dat file.
    get_dates():
        Return first and last dates.
    process_and_get():
        Process file and return initial and final dates.
    """


    def __init__(self, abs_path=None, encoding='utf-8', verbose=False, _debug=False):
        if abs_path is None:
            self._abs_path = {}
        else:
            self._abs_path = abs_path
        self._encoding = encoding
        self._verbose = verbose
        self._debug = _debug

        self._file_path = None
        self._first_date = None
        self._last_date = None

    # MARK: Read
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


    @staticmethod
    def _clean_line(txt, multilines=False):
        sub = {
            'comments': (r'\*\*.*$', ''),
            'tabs': (r'\t{1,}', ' '),
            'asterisks': (r'(\s)\*(\w)', r"\g<1>\g<2>"),
            'initial spaces': (r'^\s+',''),
            'final spaces': (r'\s+$',''),
        }

        if multilines:
            flag = re.MULTILINE
        else:
            flag = 0

        for (search_,replace_) in sub.values():
            txt = re.sub(search_, replace_, txt, flags=flag)
        txt = txt.lstrip(r'\*')

        if multilines:
            txt = DatDates._remove_triggers(txt)

        return txt

    @staticmethod
    def _remove_triggers(lines):
        while True:
            start_index = lines.rfind('\nTRIGGER')
            end_index = lines.find('\nEND_TRIGGER', start_index)
            if start_index == -1 or end_index == -1:
                return lines
            lines = lines[:start_index] + lines[end_index + len('\nEND_TRIGGER'):]


    def _get_code(self, file_path, keyword=None):
        """Read file and return code after keyword."""

        txt = self._safe_file_read(file_path)
        txt = DatDates._clean_line(txt, multilines=True)

        if keyword is None:
            return txt

        if f'\n{keyword}\n' not in txt:
            msg = f'{keyword} not found in file.'
            raise ValueError(msg)

        txt = txt.split(f'\n{keyword}\n')[1:]
        if len(txt) > 1:
            msg = f'More than one {keyword} found.'
            raise ValueError(msg)

        return txt[0]


    @staticmethod
    def _is_float(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _get_key(line):

        if len(line) == 0:
            return None
        if line[0]=="'":
            return None
        if line[:3]=="BG ":
            return None
        split_line = line.split()
        if '*' in split_line[0]:
            return None
        if ':' in split_line[0]:
            return None
        if DatDates._is_float(split_line[0]):
            return None
        return split_line


    def _resolve_relative_path(self, relative_path):
        relative_path = relative_path.replace('\\', '/')
        for k,v in self._abs_path.items():
            if relative_path.startswith(k):
                path_ = re.sub(f'^{k}', v, relative_path)
                return Path(path_)
        path_ = self._file_path.parent / relative_path
        return path_.resolve()


    # MARK: Search Dates
    def _search_dates(self, code, is_include=True):
        if isinstance(code, list):
            return self._search_date_in_lines(
                lines=code,
                is_include=is_include)

        try:
            with open(code, "r", encoding=self._encoding) as lines:
                return self._search_date_in_lines(
                    lines=lines,
                    is_include=is_include)
        except UnicodeDecodeError:
            if self._verbose:
                code = Path(code)
                print(f'Error reading: {code.name}. Trying different encoding.')
            for encoding in [e for e in ENCODINGS if e != self._encoding]:
                try:
                    with open(code, "r", encoding=encoding) as lines:
                        result = self._search_date_in_lines(
                            lines=lines,
                            is_include=is_include)
                    self._encoding = encoding
                    if self._verbose:
                        print(f'Changed encoding to {self._encoding}.')
                    return result
                except: #pylint: disable=bare-except
                    pass
        raise UnicodeEncodeError('Could not open file.')


    def _search_date_in_lines(self, lines, is_include=True):
        check_first_key = is_include

        current_key = ''
        trigger_depth = 0
        for line in lines:
            if not isinstance(lines, list):
                line = DatDates._clean_line(line)
                if line == '':
                    continue
            line = DatDates._get_key(line)
            if line is None:
                continue

            if line[0] == 'TRIGGER':
                trigger_depth += 1
            elif line[0] == 'END_TRIGGER':
                trigger_depth -= 1
            if trigger_depth > 0:
                continue

            if check_first_key:
                if line[0] in VFP_keys + WELL_keys:
                    if self._verbose:
                        print(f'  Found {line[0]} => skipped reading file.')
                    return True
                check_first_key = False

            if line[0] == 'INCLUDE':
                if self._debug:
                    timer = Timer(0.1)
                include_name = line[1][1:-1].replace('\\','/').split('/')[-1]

                if current_key in VFP_keys + WELL_keys:
                    if self._verbose:
                        print(f'Current key {current_key} => skipped reading {include_name}.')
                    current_key = line[0]
                    if self._debug:
                        timer.tock(f'Skipped reading {include_name}')
                    continue

                include_path = self._resolve_relative_path(line[1][1:-1])
                if self._verbose:
                    print(f'Reading {include_path.name}')

                if not include_path.is_file():
                    print(f'File not found: {include_path}')
                    if self._debug:
                        timer.tock(f'File not found: {include_name}')
                    continue

                if not self._search_dates(include_path, is_include=True):
                    if self._debug:
                        timer.tock(f'Read STOP: {include_name}')
                    return False

                if self._debug:
                    timer.tock(f'Read: {include_name}')

            current_key = line[0]
            if current_key in ['DATE','TIME']:
                if self._first_date is None:
                    self._first_date = line[1:]
                self._last_date = line[1:]
            elif current_key == 'STOP':
                if self._verbose:
                    print('Found STOP.')
                return False
        return True


    # MARK: Process
    def process(self, file_path):
        """Search initial and final DATE."""
        self._file_path = None

        if self._verbose:
            print(f'Processing {file_path}.')

        file_path = Path(file_path)
        if not file_path.is_file():
            msg = f'File not found: {file_path}.'
            raise ValueError(msg)

        self._file_path = file_path

        code = self._get_code(file_path=file_path, keyword='RUN')

        self._first_date = None
        self._last_date = None

        self._search_dates(
            code=code.split('\n'),
            is_include=False,
        )


    def process_log(self, file_path):
        """
        Return initial and final DATE in a log file.

        Assumptions:
        - Dates are expressed as 'YYYY MM DD', separated by either
        /, \\, ., -, : or single space.
        - There are spaces before and after the date.
        - Dates are in the same position (column) in the log lines.
        - Dates are in ascending order.
        """
        txt = self._safe_file_read(file_path).split('\n')

        date_pattern = r'\s(\d{4})[ /\\.:-](\d{2})[ /\\.:-](\d{2})\s'
        results = []
        for line in txt:
            for match in re.finditer(date_pattern, line):
                start_index = match.start()
                date_str = ' '.join(match.groups())
                results.append((date_str, start_index))

        start_indices = [start_index for _, start_index in results]
        index_counts = Counter(start_indices)
        most_common_index, _ = index_counts.most_common(1)[0]
        dates = [datetime.strptime(date, '%Y %m %d')
                 for date, pos in results if pos == most_common_index]

        dates_filter = []
        for d1,d2 in zip(dates[::-1][:-1], dates[::-1][1:]):
            if d1 >= d2:
                dates_filter.append(d1)
            elif len(dates_filter) > 0:
                if d1 <= dates_filter[-1]:
                    dates_filter.append(d1)
        if len(dates_filter) > 0:
            if dates[0] <= dates_filter[-1]:
                dates_filter.append(dates[0])

        if len(dates_filter) > 0:
            return self.date_to_str(dates_filter[-1]), self.date_to_str(dates_filter[0])
        return None, None


    def get_progress(self, log_path=None):
        """Check simulation progress."""
        if self._first_date is None or self._last_date is None:
            return None

        if log_path is None:
            if self._file_path is None:
                return None
            log_path = self._file_path.with_suffix('.log')
        log_path = Path(log_path)
        if not log_path.is_file():
            return None

        _, current_date = self.process_log(log_path)
        if current_date is None:
            return None

        first = self.str_to_date(' '.join(self._first_date))
        last = self.str_to_date(' '.join(self._last_date))
        current = self.str_to_date(current_date)

        if last > first:
            if current < first:
                return 0.0
            if current > last:
                return 1.0
            return (current - first) / (last - first)
        return None


    # MARK: Convert
    @staticmethod
    def str_to_date(date_str):
        """Convert CMG format string to date."""
        fractional_day = '0'
        if '.' in date_str:
            date_str, fractional_day = date_str.split('.')
        date = datetime.strptime(date_str, '%Y %m %d')
        days = float('0.'+fractional_day)
        return date + timedelta(days=days)

    @staticmethod
    def date_to_str(date):
        """Convert date to CMG format string."""
        def _fraction_of_day(date_time):
            seconds = date_time.hour * 3600
            seconds += date_time.minute * 60
            seconds += date_time.second
            seconds += date_time.microsecond / 1E6
            seconds_in_a_day = 24 * 60 * 60
            return seconds / seconds_in_a_day

        date_str = date.strftime('%Y %m %d')
        fractional_day = _fraction_of_day(date)
        if fractional_day > 0:
            date_str += f'{fractional_day:10f}'.strip().strip('0')

        return date_str


    def _add_time(self):
        first_date = DatDates.str_to_date(' '.join(self._first_date))

        days = float(self._last_date[0])
        last_date = first_date + timedelta(days=days)
        last_date_str = DatDates.date_to_str(last_date)

        self._last_date = last_date_str.split()


    # MARK: Get
    def get_dates(self):
        """Return initial and final dates of the last processed file."""
        if len(self._last_date) == 1:
            self._add_time()
        return ' '.join(self._first_date), ' '.join(self._last_date)


    def set_dates(self, first_date, last_date):
        """Set initial and final dates."""
        if first_date is not None:
            first_date = first_date.split()
        if last_date is not None:
            last_date = last_date.split()
        self._first_date = first_date
        self._last_date = last_date


    def process_and_get(self, file_path):
        """Process file and return initial and final dates."""
        self.process(file_path)
        return self.get_dates()


def execute(args):
    """Execute code on the provided arguments."""
    absolute_dict = json.loads(args.absolute) if args.absolute else {}

    dat_date = DatDates(
        encoding=args.encoding,
        abs_path=absolute_dict,
        verbose=args.verbose == 1,
    )
    date_ini, date_end = dat_date.process_and_get(args.file_path)

    if args.progress == 1:
        p = dat_date.get_progress(args.log_path)
        print(p)
    else:
        print(f'{date_ini}, {date_end}')


def parse_arguments():
    """Parse command-line arguments"""
    desc = "Process a file with specified encoding and absolute arguments."
    parser = argparse.ArgumentParser(description=desc)

    desc = "Path to the input file."
    parser.add_argument("file_path", type=str, help=desc)

    desc = "Encoding of the input file (default: utf-8)."
    parser.add_argument("--encoding", type=str, default="utf-8", help=desc)

    desc = "Absolute paths arguments as a JSON-formatted string "
    desc += "(e.g., '{\"\\folder\": \"\\\\server.com\\folder_a\"}') "
    desc += "(default: '{ }')"
    parser.add_argument("--absolute", type=str, default="{ }", help=desc)

    desc = "Progress flag: 1=True (default: False)."
    parser.add_argument("--progress", type=int, default=0, help=desc)

    desc = "Path to the log file."
    parser.add_argument("--log_path", type=str, default=None, help=desc)

    desc = "Verbose flag: 1=True (default: False)."
    parser.add_argument("--verbose", type=int, default=0, help=desc)

    return parser.parse_args()


def _error_msg():
    msg = "Error: Missing arguments."
    msg += "\nUsage: python dat_dates.py <file_path> "
    msg += "[--encoding <encoding>] [--absolute <absolute_json>] "
    msg += "[--progress <1>] [--log_path <log_path>] "
    msg += "[--verbose <1>]"
    print(msg)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        _error_msg()
        sys.exit(1)
    execute(parse_arguments())
