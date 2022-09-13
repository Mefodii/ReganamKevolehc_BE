import json


class YTDownloadSettings:
    def __init__(self, file_path):
        data = self.get_json_data(file_path)
        self.json_data = data
        self.input_file = data["input_file"]
        self.output_directory = data["output_directory"]
        self.resources_path = data["resources_path"]

    @staticmethod
    def get_json_data(file_path):
        with open(file_path) as json_file:
            return json.load(json_file)
