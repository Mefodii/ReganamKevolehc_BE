import codecs
import glob
import json
import os
import shutil
import time
from os import listdir
from os.path import isfile, join, isdir
# from stat import S_ISREG, ST_CTIME, ST_MODE
from typing import Any

PATH = "path"
FILENAME = "filename"
EXTENSION = "extension"
CR_TIME = "cr_time"
CR_TIME_READABLE = "cr_time_r"

ENCODING_UTF8 = "utf-8"


class File:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.extension = name.split(".")[-1]
        self.cr_time = None
        self.cr_time_r = None

    def get_abs_path(self) -> str:
        return str(os.path.join(self.path, self.name))

    def get_plain_name(self) -> str:
        """
        :return: file name without extension
        """
        name = ".".join(self.name.split(".")[0:-1])
        return name

    @classmethod
    def from_abs_path(cls, abs_path: str):
        args = os.path.split(abs_path)
        obj = cls(args[1], args[0])
        return obj

    def read(self, encoding: str = None) -> list[str]:
        return read(self.get_abs_path(), encoding)

    def write(self, data: list[Any], encoding: str = None):
        return write(self.get_abs_path(), data, encoding)

    def rename(self, new_name: str):
        """
        Change the name of file and rename it on OS.
        The path remains same.
        :param new_name:
        :return:
        """
        new_abs_path = f"{self.path}\\{new_name}"
        os.rename(self.get_abs_path(), new_abs_path)
        self.name = new_name

    def copy(self, dest: str):
        return copy(self.get_abs_path(), dest)

    def delete(self):
        return delete(self.get_abs_path())

    def obtain_creation_time(self):
        """
        Append file creation time for each received file. Mutated.
        :return:
        """
        creation_time = os.path.getctime(self.get_abs_path())
        self.cr_time = creation_time
        self.cr_time_r = time.ctime(creation_time)

    def __repr__(self):
        return f"{self.get_abs_path()}"


def read(file_name: str, encoding: str = None) -> list[str]:
    """
    Fully read file as list of string
    :param file_name:
    :param encoding:
    :return:
    """
    data = []
    with codecs.open(file_name, 'r', encoding) as input_file:
        for input_line in input_file:
            data.append(input_line.replace("\n", ""))
    return data


def read_json(file_path: str) -> dict:
    """
    Read file which is in a JSON format
    :param file_path:
    :return: dict representation of file content
    """
    with open(file_path) as json_file:
        return json.load(json_file)


def write_json(output_path: str, data: dict | list) -> None:
    """
    Dumbs data to the output file in a json format.

    Sorted by keys.

    Indent: 4
    :param output_path:
    :param data:
    :return:
    """
    with open(output_path, 'w') as outfile:
        # Note: 2023.10.23 - unicode output is displayed as "\u***", atm it seems not a good idea to make file readable.
        # src - https://stackoverflow.com/questions/18337407/
        # saving-utf-8-texts-with-json-dumps-as-utf-8-not-as-a-u-escape-sequence
        json.dump(data, outfile, sort_keys=True, indent=4)


def write(output_path: str, data: list[Any], encoding: str = None) -> None:
    """
    Write str representation of each element from "data" to the output_path.

    Line separator: "\\\\n".
    :param output_path:
    :param data:
    :param encoding:
    :return:
    """
    with codecs.open(output_path, 'w', encoding) as result_file:
        for result_line in data:
            result_file.write(str(result_line) + "\n")


def append(output_path: str, data: list[Any] | Any):
    """
    Append str representation of each element from "data" to the output_path.

    If "data" is not a list, then append str representation of "data".

    Line separator: "\\\\n".

    Create output_path if it doesn't exist.
    :param output_path:
    :param data:
    :return:
    """
    with codecs.open(output_path, 'a+', ENCODING_UTF8) as result_file:
        if isinstance(data, list):
            for result_line in data:
                result_file.write(str(result_line) + "\n")
        else:
            result_file.write(str(data) + "\n")


def get_file_extension(path: str, name: str) -> str:
    """
    Get the extension of the first file with matches the criteria.

    Raise exception if file not found.
    :param path:
    :param name:
    :return: file extension
    """
    pattern = os.path.join(path, name + '.*')
    for infile in glob.glob(pattern):
        return infile.split(".")[-1]

    raise Exception(f"No file found: {pattern}")


def exists(file_path: str) -> bool:
    """
    :param file_path:
    :return: true if file exists
    """
    return os.path.isfile(file_path)


def dir_exists(dir_path: str) -> bool:
    """
    :param dir_path:
    :return: true if dir exists
    """
    return os.path.isdir(dir_path)


def delete(file_path: str):
    """
    Delete file from the current system
    :param file_path:
    :return:
    """
    os.remove(file_path)


def copy(src: str, dest: str):
    """
    Copy a file from source to destination, using shutil library
    If dest is a folder, then a file with same name as in src will be created
    :param src: absolute path (including filename)
    :param dest: absolute path (including filename)
    :return:
    """
    return shutil.copy2(src, dest)


def list_files(path: str, recursive: bool = False, with_creation_time: bool = False, depth: int = 0) -> list[File]:
    """
    Return a list of files from specified path.

    :param path:
    :param recursive:
    :param depth: keeping track of recursion level
    :param with_creation_time: True -> extract creation time of the file
    :return:
    """
    files = [File(f, path) for f in listdir(path) if isfile(join(path, f))]

    if recursive:
        for directory in list_dirs(path):
            files += list_files(directory, recursive=True, with_creation_time=with_creation_time, depth=depth + 1)

    # Append creation when out of all recursion levels
    if with_creation_time and depth == 0:
        [f.obtain_creation_time() for f in files]

    return files


def list_dirs(path: str) -> list[str]:
    """
    Return a list of folder from specified path in absolute form (path\\\\<result>).

    Not recursive.

    :param path:
    :return:
    """
    return [join(path, f) for f in listdir(path) if isdir(join(path, f))]
