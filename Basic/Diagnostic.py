import colorama
from colorama import Fore

from Basic.Location import Location
from enum import Enum

colorama.init(autoreset=True)


class DiagnosticKind(Enum):
    ERROR = "error"
    WARNING = "warning"


class Diagnostic(Exception):
    def __init__(self, msg: str, location: Location, kind: DiagnosticKind):
        self.msg = msg
        self.location = location
        self.kind = kind

    def dump(self):
        """输出信息"""
        print(f"{self.location}: ", end="")
        if self.kind == DiagnosticKind.ERROR:
            print(Fore.RED + "错误", end=": ")
        elif self.kind == DiagnosticKind.WARNING:
            print(Fore.YELLOW + "警告", end=": ")
        print(self.msg)
        for loc in self.location:
            lines = Location.lines[loc["filename"]]
            row = loc["lineno"] - 1
            col = loc["col"] - 1
            if row >= len(lines):
                continue
            prefix = f"{loc['lineno']}|"
            print(prefix, lines[row].rstrip())
            print(" " * len(prefix), " " * col + "^" * loc["span_col"])


class Error(Diagnostic):
    def __init__(self, msg: str, location: Location):
        super().__init__(msg, location, DiagnosticKind.ERROR)
