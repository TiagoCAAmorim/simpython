"""
Python script to process a schedule file and generate daily entries for each date in the file.

process(input_file_path, output_file_path, encoding='utf-8'):
    Reads a schedule file and generates daily entries for each date.
    Args:
        input_file_path (str): Path to the input schedule file.
        output_file_path (str): Path to the output file where processed data will be saved.
        encoding (str): Encoding of the input file. Default is 'utf-8'.
"""
import sys
from datetime import datetime, timedelta


def _date_to_str(date):
    """Converts a datetime object to a string in the format YYYY-MM-DD."""
    return f"DATE {date.year} {date.month} {date.day}\n"


def process(input_file_path, output_file_path, delta_days=1, encoding='utf-8'):
    """
    Reads a schedule file and generates daily entries for each date.
    Args:
        input_file_path (str): Path to the input schedule file.
        output_file_path (str): Path to the output file where processed data will be saved.
        encoding (str): Encoding of the input file. Default is 'utf-8'.
    """
    current_date = None
    last_date = None
    output = []

    with open(input_file_path, 'r', encoding=encoding) as input_file:
        for line in input_file:
            if line.strip().startswith("DATE"):
                parts = line.split()
                year, month, day = int(parts[1]), int(parts[2]), int(parts[3])
                new_date = datetime(year, month, day)

                if current_date is None:
                    current_date = new_date
                    output.append(_date_to_str(current_date))
                else:
                    if new_date < current_date:
                        msg = f"Dates are not in chronological order: {current_date} -> {new_date}"
                        raise ValueError(msg)
                    while current_date < new_date:
                        current_date += timedelta(days=delta_days)
                        current_date = min(current_date, new_date)
                        output.append(_date_to_str(current_date))
                    # if current_date > new_date:
                    #     current_date = new_date
                        # output.append(_date_to_str(new_date))

                last_date = new_date
            else:
                output.append(line)

        if last_date and current_date <= last_date:
            while current_date <= last_date:
                output.append(_date_to_str(current_date))
                current_date += timedelta(days=1)

    with open(output_file_path, 'w', encoding=encoding) as output_file:
        output_file.writelines(output)


def main():
    """Main function to execute the script."""
    if len(sys.argv) == 1:
        print(__doc__)
    if len(sys.argv) != 3:
        print("Usage: python schedule_to_daily.py <input_file_path> <output_file_path>")
        sys.exit(1)

    input_file_path = sys.argv[1]
    output_file_path = sys.argv[2]
    process(input_file_path, output_file_path, encoding='utf-8')


if __name__ == "__main__":
    main()
