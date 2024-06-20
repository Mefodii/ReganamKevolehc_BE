import math
import os
import re
from typing import Tuple

# noinspection PyPackageRequirements
import ffmpeg

from constants.enums import FileExtension
from utils import file

METADATA_HEADER = ";FFMETADATA1"
BITRATE_TOLERANCE = 300000  # 300Kb


class Ffmpeg:
    @staticmethod
    def merge_audio_and_video(files_path: str, audio: str, video: str, merged: str):
        audio_abs_path = files_path + "\\" + video
        video_abs_path = files_path + "\\" + audio
        merged_abs_path = files_path + "\\" + merged
        temp_merged_file = files_path + "\\merged." + FileExtension.MKV.value

        merge_command = "ffmpeg" \
                        " -i " + video_abs_path + \
                        " -i " + audio_abs_path + \
                        " -c:v copy -c:a copy " + temp_merged_file
        os.system(merge_command)
        os.remove(audio_abs_path)
        os.remove(video_abs_path)
        os.rename(temp_merged_file, merged_abs_path)

    @staticmethod
    def add_tags(file_abs_path: str, tags_dict: dict, loglevel: str = None):
        file_format = file_abs_path.split(".")[-1]

        file_path = "\\".join(file_abs_path.split("\\")[:-1])
        temp_abs_path = file_path + "\\temptags." + file_format
        tag_abs_path = file_path + "\\tags." + file_format

        os.rename(file_abs_path, temp_abs_path)

        tags = []
        for key, value in tags_dict.items():
            tag_value = value.replace("\"", "\\\"").replace("\'", "\"'\"")

            # The titles with symbol "&" and between quotes will be replaced with "^&"
            # In that way ffmpeg command will be generated correctly
            if "&" in file_abs_path and "\"" in tag_value:
                splitted = tag_value.split("\"")
                for i in range(1, len(splitted), 2):
                    if i != len(splitted):
                        splitted[i] = splitted[i].replace("&", "^&")
                tag_value = "\"".join(splitted)

            tag_str = "-metadata " + key + "=\"" + tag_value + "\""
            tags.append(tag_str)

        tags_command = " ".join(tags)
        command = f"ffmpeg -i \"{temp_abs_path}\" -c copy {tags_command} \"{tag_abs_path}\""
        if loglevel:
            command += f" -hide_banner -loglevel {loglevel}"
        os.system(command)

        os.rename(tag_abs_path, file_abs_path)
        os.remove(temp_abs_path)

    # Deprecated
    @staticmethod
    def read_metadata_old(file_abs_path: str, loglevel: str = None) -> list[str]:
        # Deprecated
        file_format = file_abs_path.split(".")[-1]
        file_path = "\\".join(file_abs_path.split("\\")[:-1])

        temp_abs_path = file_path + "\\tempmeta." + file_format
        temp_metadata_file = file_path + "\\tempmetadata.txt"

        os.rename(file_abs_path, temp_abs_path)

        read_metadata_command = f"ffmpeg -i \"{temp_abs_path}\" -f ffmetadata \"{temp_metadata_file}\""
        if loglevel:
            read_metadata_command += f" -hide_banner -loglevel {loglevel}"

        os.system(read_metadata_command)
        os.rename(temp_abs_path, file_abs_path)

        metadata = file.read(temp_metadata_file, file.ENCODING_UTF8)
        os.remove(temp_metadata_file)
        return metadata

    # Deprecated
    @staticmethod
    def read_metadata_json_old(file_abs_path: str, loglevel: str = None) -> dict:
        # Deprecated
        raw_metadata = Ffmpeg.read_metadata_old(file_abs_path, loglevel)
        metadata = {}
        attr_match = "\\S*="
        attr_name = None
        attr_value = None

        for line in raw_metadata:
            parsed_line = re.search(attr_match, line)
            if line == METADATA_HEADER:
                pass
            else:
                if parsed_line and len(parsed_line.group()) > 1:
                    if attr_name:
                        metadata[attr_name] = attr_value

                    attr_name = parsed_line.group().replace("=", "").upper()
                    attr_value = "=".join(line.split("=")[1:])
                else:
                    attr_value += "\n" + line
        metadata[attr_name] = attr_value

        return metadata

    @staticmethod
    def read_metadata(file_abs_path: str) -> dict:
        raw_metadata: dict[str, str] = ffmpeg.probe(file_abs_path)["format"]["tags"]
        metadata = {}
        for k, v in raw_metadata.items():
            metadata[k.upper()] = v

        return metadata

    @staticmethod
    def tags_equal(t1: dict, t2: dict) -> bool:
        if len(t1) != len(t2):
            return False

        for k, v in t1.items():
            v2 = t2.get(k)
            if v2 is None:
                return False

            if str(v) != str(v2):
                return False

        return True

    @staticmethod
    def get_video_resolution(video_abs_path: str) -> Tuple[int, int]:
        output = os.popen(f"ffprobe -v error -select_streams v:0 "
                          f"-show_entries stream=width,height -of csv=s=x:p=0 \"{video_abs_path}\"").read()
        width, height = output.split("x")
        return int(width), int(height)

    @staticmethod
    def compare_resolution(w1: int, h1: int, w2: int = None, h2: int = None) -> int:
        """
        Other video may have width of height None.

        On comparison None values are considered equal to value from first video
        :param w1: width of first video
        :param h1: height of first video
        :param w2: width of other video
        :param h2: height of other video
        :return: 1 if first video is larger than other, -1 if smaller, 0 if equal
        """

        if w2 is None and h2 is None:
            raise Exception("Both height and width are None")

        w2_val = w2 if w2 else w1
        h2_val = h2 if h2 else h1

        if w1 == w2_val and h1 == h2_val:
            return 0  # video1 == video2

        if w1 >= w2_val or h1 >= h2_val:
            return 1  # video1 > video2

        if w1 <= w2_val or h1 <= h2_val:
            return -1  # video1 < video2

        raise Exception("Comparison for when one parameter is bigger and other small not implemented.")

    @staticmethod
    def resize(file_abs_path: str, height: int = None, width: int = None, scale_bitrate: bool = False):
        if not height and not width:
            raise Exception("Height, width is None. At least one should have a value")

        original_width, original_height = Ffmpeg.get_video_resolution(file_abs_path)
        needs_resize = Ffmpeg.compare_resolution(original_width, original_height, width, height) == 1
        if not needs_resize:
            print("File original size is already equal or less than resize value. Resize cancelled.\n"
                  f"Original resolution {original_width}x{original_height}. Resize: {width}x{height}")
            return

        h = height if height else -1
        w = width if width else -1

        original_bitrate = -1
        target_bitrate = -1
        if scale_bitrate:
            original_bitrate = Ffmpeg.get_video_bitrate(file_abs_path)
            ratio = height / original_height if height else width / original_width
            target_bitrate = math.floor(original_bitrate * ratio)

        file_format = file_abs_path.split(".")[-1]
        file_path = "\\".join(file_abs_path.split("\\")[:-1])
        temp_resize_file = file_path + "\\temp_resized." + file_format

        command = f"ffmpeg -hwaccel cuda -i \"{file_abs_path}\" -vf scale={w}:{h} -c:v h264_nvenc "
        if scale_bitrate:
            command += f"-b:v {target_bitrate} "
        command += f"{temp_resize_file}"
        os.system(command)

        # Delete resized file if it is still larger or equal to original file
        original_size = os.path.getsize(file_abs_path)
        resized_size = os.path.getsize(temp_resize_file)

        if resized_size >= original_size:
            os.remove(temp_resize_file)
            print(f"Resized file ({resized_size}) is not smaller than original file ({original_size})."
                  f" Resize cancelled")
        else:
            print(f"Resized from: ({original_size}) to ({resized_size}).")
            if scale_bitrate:
                final_bitrate = Ffmpeg.get_video_bitrate(temp_resize_file)
                print(f"Bitrate changed from: {original_bitrate} to {final_bitrate}. Target bitrate: {target_bitrate}")
            os.remove(file_abs_path)
            os.rename(temp_resize_file, file_abs_path)

    @staticmethod
    def get_video_bitrate(video_abs_path: str) -> int:
        # Source: https://superuser.com/questions/1106343/determine-video-bitrate-using-ffmpeg
        output = os.popen(f"ffprobe -v quiet -select_streams v:0 -show_entries format=bit_rate "
                          f"-of default=noprint_wrappers=1 \"{video_abs_path}\"").read()
        return int(output.replace("bit_rate=", ""))

    @staticmethod
    def is_valid_bitrate_change(file_bitrate: int, desired_bitrate: str) -> bool:
        bitrate = int(desired_bitrate.upper().replace("K", "000").replace("M", "000000"))
        print(bitrate)
        return file_bitrate - BITRATE_TOLERANCE > bitrate

    @staticmethod
    def change_bitrate(file_abs_path: str, bitrate: str):
        original_bitrate = Ffmpeg.get_video_bitrate(file_abs_path)
        needs_bitrate = Ffmpeg.is_valid_bitrate_change(original_bitrate, bitrate)

        if not needs_bitrate:
            print(f"File original bitrate is out of bounds withing acceptable tolerance of: {BITRATE_TOLERANCE}. "
                  f"Resize cancelled.\nOriginal bitrate {original_bitrate}. Resize: {bitrate}")
            return

        file_format = file_abs_path.split(".")[-1]
        file_path = "\\".join(file_abs_path.split("\\")[:-1])
        temp_resize_file = file_path + "\\temp_resized." + file_format

        # -b:v 1M (will try to set bitrate to 1 megabyte)
        command = f"ffmpeg -hwaccel cuda -i \"{file_abs_path}\" -c:v h264_nvenc -b:v {bitrate} {temp_resize_file}"
        os.system(command)

        # Delete resized file if it is still larger or equal to original file
        original_size = os.path.getsize(file_abs_path)
        resized_size = os.path.getsize(temp_resize_file)

        if resized_size >= original_size:
            os.remove(temp_resize_file)
            print(f"Resized file ({resized_size}) is not smaller than original file ({original_size})."
                  f" Resize cancelled")
        else:
            print(f"Resized from: ({original_size}) to ({resized_size}).")
            os.remove(file_abs_path)
            os.rename(temp_resize_file, file_abs_path)
