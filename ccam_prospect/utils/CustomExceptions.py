class NonStandardExposureTimeException(Exception):
    pass


class MismatchedExposureTimeException(Exception):
    pass


class NonStandardHeaderException(Exception):
    pass


class CancelExecutionException(Exception):
    pass


class InputFileNotFoundException(Exception):
    def __init__(self, file):
        self.file = file


