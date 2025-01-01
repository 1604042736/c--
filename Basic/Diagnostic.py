from typing import Union
import colorama
from colorama import Fore

from Basic.Location import Location
from enum import Enum


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
        if self.kind == DiagnosticKind.ERROR:
            print(Fore.RED + "错误", end=": ")
        elif self.kind == DiagnosticKind.WARNING:
            print(Fore.YELLOW + "警告", end=": ")
        print(self.msg)
        indent = " " * 4
        for loc in self.location:
            filename = loc["filename"]
            lines = Location.lines[filename]
            row = loc["lineno"] - 1
            col = loc["col"] - 1
            if row >= len(lines):
                continue
            prefix = indent * 2 + f"{loc['lineno']}|"
            print(indent + f"{self.location}:")
            print(prefix, lines[row].rstrip())
            print(" " * len(prefix), " " * col + "^" * loc["span_col"])


class Error(Diagnostic):
    def __init__(self, msg: str, location: Location):
        super().__init__(msg, location, DiagnosticKind.ERROR)


class Diagnostics(Exception):
    def __init__(self, diagnostic_list: list[Error]):
        self.list = diagnostic_list

    def __add__(self, other: Union[list[Diagnostic], "Diagnostics"]):
        diagnostic_list = self.list
        if isinstance(other, Diagnostics):
            diagnostic_list += other.list
        else:
            diagnostic_list += other
        return Diagnostics(diagnostic_list)

    def __bool__(self):
        return bool(self.list)

    def dump(self):
        for diagnostic in self.list:
            diagnostic.dump()
