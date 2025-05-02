"""
Module to get dates from CMG dat files.

Functions
---------
get_dates_from_dat(file_path, abs_path=None, encoding='utf-8', verbose=False):
    Get list of dates from a CMG dat file.
get_dates_from_dat_data(data, verbose=False):
    Get list of dates from a CMG dat file processed data.
to_date(date_str):
    Convert CMG format string to datetime.
to_str(date):
    Convert date to CMG format string.
"""
import re
from datetime import datetime, timedelta
from collections import Counter

try:
    from rsimpy.cmg.datreader.dat_parser import DatParser
    from rsimpy.cmg.datreader.common import safe_file_read
except ImportError:
    from dat_parser import DatParser
    from common import safe_file_read


def get_from_dat(file_path, abs_path=None, encoding='utf-8', verbose=False, _debug=False):
    """
    Get list of dates from a CMG dat file.

    Parameters
    ----------
    file_path : str
        Path to the dat file.
    abs_path : dict
        Dictionary with changes to absolute pathes. Keys are the
        strings to be searched in the start of the include path,
        and values are the strings to replace any positive search.
        If None, no search is performed. Default: None.
    encoding : str
        File encoding. Default: 'utf-8'.
    verbose : bool
        Print messages. Default: False.

    Returns
    -------
    tuple
        First and last dates in the format 'YYYY MM DD'.
    """
    parser = DatParser(
        abs_path=abs_path,
        encoding=encoding,
        ignore=['TITLE1','GRID','ROCKFLUID','INITIAL','NUMERICAL','VFP_keys','TRIGGER_keys'],
        verbose=verbose,
        _debug=_debug)
    parser.process(file_path=file_path)

    return get_from_dat_data(parser.get(), verbose=verbose)


def get_from_dat_data(data, verbose=False): # pylint: disable=too-many-branches
    """
    Get list of dates from a CMG dat file processed data.

    Parameters
    ----------
    data : dict of lists
        Dictionary with the processed data from the dat file.
        This is the output of the DatParser.get() method.
    verbose : bool
        Print messages. Default: False.

    Returns
    -------
    list
        Dates as datetime objects.
    """
    if 'RUN' in data:
        data = data['RUN']
    else:
        if verbose:
            print('No RUN section found.')
        if 'No section' in data:
            data = data['No section']
        else:
            raise ValueError("No RUN or 'No section' found. Invalid data.")

    dates = []
    for line in data:
        if line[0] == 'DATE':
            date = to_date(line[1:])
            if len(dates) > 0:
                if date < dates[-1]:
                    msg = "Dates are not in ascending order."
                    msg += f" Found {to_str(date)} after {to_str(dates[-1])}."
                    raise ValueError(msg)
            dates.append(date)
        elif line[0] == 'TIME':
            delta_time = float(line[1])
            if len(dates) == 0:
                raise ValueError("No DATE found before TIME. Invalid data.")
            if delta_time <= 0:
                msg = "TIME keyword should be positive."
                msg += f" Found {line[1]}."
                raise ValueError(msg)
            date = dates[0] + timedelta(days=delta_time)
            dates.append(date)

    if len(dates) == 0:
        if verbose:
            print('No DATE keywords found.')

    return dates


def to_date(date_lst):
    """Convert CMG format string to datetime."""
    day_str = date_lst[2]
    fractional_day = '0'
    if '.' in day_str:
        day_str, fractional_day = day_str.split('.')
    date = datetime.strptime(f'{date_lst[0]} {date_lst[1]} {day_str}', '%Y %m %d')
    days = float('0.'+fractional_day)
    return date + timedelta(days=days)


def to_str(date):
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


def process_log(file_path):
    """
    Return dates from an ascii file.

    Assumptions:
    - Dates are expressed as 'YYYY M D', separated by either
    /, \\, ., -, : or single space.
    - There are spaces before and after the date.
    - Dates are in the same position (column) in the log lines.
    - Dates are in ascending order.
      - Succesive equal dates are allowed.
    """
    txt = safe_file_read(file_path).split('\n')

    date_pattern = r'\s(\d{4})[ /\\.:-](\d{1,2})[ /\\.:-](\d{1,2})\s'
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

    if len(dates_filter) == 0:
        raise ValueError("No dates found in the log file.")
    return dates_filter


if __name__ == "__main__":
    print(__doc__)

    d = process_log('tests/_no_sync/ex/dat/base_case_bo.out')
    print(len(d))
    print(d[:5])
    print()
    print(d[-5:])







#     def get_progress(self, log_path=None):
#         """Check simulation progress."""
#         if self._first_date is None or self._last_date is None:
#             return None

#         if log_path is None:
#             if self._file_path is None:
#                 return None
#             log_path = self._file_path.with_suffix('.log')
#         log_path = Path(log_path)
#         if not log_path.is_file():
#             return None

#         _, current_date = self.process_log(log_path)
#         if current_date is None:
#             return None

#         first = self.to_date(' '.join(self._first_date))
#         last = self.to_date(' '.join(self._last_date))
#         current = self.to_date(current_date)

#         if last > first:
#             if current < first:
#                 return 0.0
#             if current > last:
#                 return 1.0
#             return (current - first) / (last - first)
#         return None
