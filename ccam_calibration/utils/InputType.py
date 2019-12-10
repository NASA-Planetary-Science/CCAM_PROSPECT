from enum import Enum, unique, auto


@unique
class InputType(Enum):
    FILE = auto()
    FILE_LIST = auto()
    DIRECTORY = auto()

