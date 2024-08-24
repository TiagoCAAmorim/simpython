"""
Assorted file functions
"""
import sys
import zipfile
from pathlib import Path
import pandas as pd  # pylint: disable=import-error

sys.path.insert(0, './python')


def list_files(folder_path, with_extensions=True):
    """ Returns list of files names in folder.

    Parameters
    ----------
    folder_path : str
        Path to the folder.
    with_extensions : boolean, optional
        Include extensions to the filenames.
        (default: True)

    Raises
    ------
    FileNotFoundError
        If an invalid folder path is provided.
    """
    try:
        folder_path = Path(folder_path)
        if with_extensions:
            filenames = [file.name for file in folder_path.iterdir() if file.is_file()]
        else:
            filenames = [file.stem for file in folder_path.iterdir() if file.is_file()]
        filenames.sort()
        return filenames
    except FileNotFoundError:
        print(f"Folder '{folder_path}' not found.")
        return []


def delete_files(folder_path, extensions=None, return_list=False):
    """ Delete all files in a folder.

    Parameters
    ----------
    folder_path : str
        Path to the folder.
    extensions : list of str, optional
        Limits deletion to files with extensions listed.
        (default: delete all files)
    return_list : boolean, optional
        Return list with of files deleted.

    Raises
    ------
    FileNotFoundError
        If an invalid folder path is provided.
    """
    files = []
    for f in list_files(folder_path):
        file = folder_path/f
        if (extensions is None) or (file.suffix in extensions):
            file.unlink()
            files.append(file)
    if return_list:
        return files


def save_to_csv(values, output_file_path, header=None):
    """ Create csv file with the provided data.

    Parameters
    ----------
    values : Pandas.DataFrame-like input
        Data to be saved.
    output_file_path : str
        Path of the new csv file.
    header : list of str, optional
        Names of the columns.
        (Default: [0, 1, ..., n])

    Raises
    ------
    ValueError
        Number of data columns does not match header length.
    """
    Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(values, columns=header)
    df.to_csv(output_file_path, index=True, index_label='index')


def zip_files(folder_path, file_list=None, extensions=None, file_name='archive',
              delete_original=False):
    """ Zip all files found in a folder.

    Parameters
    ----------
    folder_path : str
        Path to the output folder.
    file_list : list of str, optional
        List of files names to be added to zip file.
        (default: all files found in folder)
    extensions : list of str, optional
        Limits zip to files with extensions listed.
        (default: zip all files)
    file_name: str, optional
        Name of the zip file.
        (default: 'archive')
    delete_original: boolean, optional
        Delete original files.
        (default: False)

    Raises
    ------
    FileNotFoundError
        If an invalid folder path is provided.
    """
    with zipfile.ZipFile(folder_path/f'{file_name}.zip', 'w', zipfile.ZIP_DEFLATED) as myzip:
        if file_list is None:
            file_list = list_files(folder_path)
        for filename in file_list:
            if isinstance(filename, str):
                file = folder_path/filename
            else:
                file = filename
            if (extensions is None) or (file.suffix in extensions):
                myzip.write(file, arcname=file.name)
                if delete_original:
                    file.unlink()


if __name__ == '__main__':
    print(__doc__)
