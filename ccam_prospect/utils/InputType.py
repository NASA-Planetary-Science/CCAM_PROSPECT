from enum import Enum, unique, auto


@unique
class InputType(Enum):
    FILE = auto()
    FILE_LIST = auto()
    DIRECTORY = auto()


input_type_switcher = {
        InputType.FILE.value: InputType.FILE,
        InputType.FILE_LIST.value: InputType.FILE_LIST,
        InputType.DIRECTORY.value: InputType.DIRECTORY
    }