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
    from rsimpy.cmg.datreader import common
except ImportError:
    from dat_parser import DatParser
    import common


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
    data = common.get_section(data, 'RUN')

    dates = []
    for line in data:
        solve_dates(dates, line)

    if len(dates) == 0:
        if verbose:
            print('No DATE keywords found.')

    return dates


def solve_dates(dates, line):
    """Solve DATE or TIME keywords from the line."""
    if line[0] == 'DATE':
        date = to_date(line[1:])
        if len(dates) > 0:
            if date < dates[-1]:
                msg = "Dates are not in ascending order."
                msg += f" Found {to_str(date)} after {to_str(dates[-1])}."
                raise ValueError(msg)
        dates.append(date)
        return True
    if line[0] == 'TIME':
        delta_time = float(line[1])
        if len(dates) == 0:
            raise ValueError("No DATE found before TIME. Invalid data.")
        if delta_time <= 0:
            msg = "TIME keyword should be positive."
            msg += f" Found {line[1]}."
            raise ValueError(msg)
        date = dates[0] + timedelta(days=delta_time)
        dates.append(date)
        return True
    return False


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


def get_from_log(file_path, encoding='utf-8', verbose=False):
    """
    Return dates from an ascii file.

    Assumptions:
    - Dates are expressed as 'YYYY M D', separated by either
    /, \\, ., -, : or single space.
    - There are spaces before and after the date.
    - Dates are in the same position (column) in the log lines.
      - Only the dates in the most common position are stored.
    - Dates are in ascending order.
      - Succesive equal dates are allowed.
    """
    txt = common.safe_file_read(file_path, default=encoding).split('\n')
    results = _read_all_dates(txt)

    if len(results) == 0:
        raise ValueError("No dates found in the log file.")
    if verbose:
        print(f"Found {len(results)} possible dates in the log file.")

    dates = _filter_dates(results, verbose)
    dates_filtered = _check_dates_read(dates)

    if len(dates_filtered) == 0:
        raise ValueError("No dates found in the log file.")
    return dates_filtered


def _check_dates_read(dates):
    """Keep only the dates that are in ascending order."""
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
    return dates_filter[::-1]


def _filter_dates(results, verbose):
    """Keep only the dates that are in the most common position."""
    indexes = [x for _, x in results]
    index_counts = Counter(indexes)
    most_common_index, _ = index_counts.most_common(1)[0]
    dates = [datetime.strptime(date, '%Y %m %d')
                for date, index in results if index == most_common_index]

    if verbose:
        msg = f"{most_common_index[1]}' at position {most_common_index[0]}"
        print("Most common date separator: "+msg)
        print(f"Found {len(dates)} dates in the log file.")
    return dates


def _read_all_dates(txt):
    """Read all dates from the log file."""
    date_pattern = r'\s(\d{4})([ /\\.:-])(\d{1,2})([ /\\.:-])(\d{1,2})\s'
    results = []
    for line in txt:
        for match in re.finditer(date_pattern, line):
            if match.group(2) != match.group(4):
                continue
            sep = match.group(2)
            start_index = match.start()
            date_str = f'{match.group(1)} {match.group(3)} {match.group(5)}'
            results.append((date_str, (start_index, sep)))
    return results


def get_progress(dates, current_date, verbose=False):
    """Check simulation progress."""
    if len(dates) < 2:
        if verbose:
            print("Not enough dates to check progress.")
        return None

    first = dates[0]
    last = dates[-1]

    if last > first:
        if current_date < first:
            if verbose:
                print("Current date is before the first date.")
            return 0.0
        if current_date > last:
            if verbose:
                print("Current date is after the last date.")
            return 1.0
        return (current_date - first) / (last - first)
    if verbose:
        print("Dates are not in ascending order.")
    return None


if __name__ == "__main__":
    print(__doc__)
