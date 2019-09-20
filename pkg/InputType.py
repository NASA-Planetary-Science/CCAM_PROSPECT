from enum import Enum, unique


@unique
class InputType(Enum):
    FILE = 1
    FILE_LIST = 2
    DIRECTORY = 3

