from zipfile import ZipFile

from utils.file import exists


def zipfiles(zipfile_abs_path: str, files: list[tuple[str, str]]) -> None:
    """

    :param zipfile_abs_path:
    :param files:   tuple[0] - filename (absolute path)
                    tuple[1] - arcname (filepath / name in the archive)
    :return:
    """
    with ZipFile(zipfile_abs_path, 'w') as zip_object:
        [zip_object.write(filename, arcname) for
         filename, arcname in files]

    # Check to see if the zip file is created
    if not exists(zipfile_abs_path):
        raise Exception(f"Failed to create zip file: {zipfile_abs_path}")


def yn_prompt(question) -> bool:
    while True:
        answer = input(question + " (Y/N): ").strip().upper()
        if answer in ['Y', 'N']:
            return answer == "Y"
        else:
            print("Please enter 'Y' for Yes or 'N' for No.")


def dict_includes(parent_dict: dict, checked_dict: dict) -> bool:
    # NOTE: "class" attr in soup is list / in webdriver is space separated string
    for key, value in checked_dict.items():
        if isinstance(value, dict):
            if not dict_includes(parent_dict.get(key, {}), value):
                return False
        elif isinstance(value, list):
            t = parent_dict.get(key, [])
            if isinstance(t, str):
                t = t.split(" ")

            if not list_includes(t, value):
                return False
        elif isinstance(value, str):
            t = parent_dict.get(key, "")
            if isinstance(t, list):
                if not list_includes(t, value.split(" ")):
                    return False
            elif key == "class":
                if not list_includes(t.split(" "), value.split(" ")):
                    return False
            else:
                if t != value:
                    return False
        else:
            raise TypeError(f"Cannot parse: {value}")

    return True


def list_includes(parent_list: list, checked_list: list) -> bool:
    for val in checked_list:
        if val not in parent_list:
            return False

    return True
