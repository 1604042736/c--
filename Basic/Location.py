from typing import Iterable, TypedDict


class LocationDict(TypedDict):
    filename: str  # 文件名
    lineno: int  # 行
    col: int  # 列
    span_col: int  # 跨越的列


class Location(list[LocationDict]):
    lines: dict[str, list[str]] = {}  # 各个文件的每行内容

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.merge()

    def append(self, object: LocationDict) -> None:
        super().append(object)
        self.merge()

    def extend(self, iterable: Iterable[LocationDict]) -> None:
        super().extend(iterable)
        self.merge()

    def merge(self):
        self.sort(key=lambda a: (a["filename"], a["lineno"], a["col"], a["span_col"]))
        i = 0
        while i < len(self) - 1:
            if (  # 有交集
                self[i]["filename"] == self[i + 1]["filename"]
                and self[i]["lineno"] == self[i + 1]["lineno"]
                and self[i]["col"] <= self[i + 1]["col"] + self[i + 1]["span_col"]
                and self[i]["col"] + self[i]["span_col"] >= self[i + 1]["col"]
            ):
                self[i]["span_col"] = (
                    max(
                        self[i]["col"] + self[i]["span_col"],
                        self[i + 1]["col"] + self[i + 1]["span_col"],
                    )
                    - self[i]["col"]
                )
                self.pop(i + 1)
            i += 1

    def __str__(self):
        s = []
        cur_filename = None
        for loc in self:
            if cur_filename == None or loc["filename"] != cur_filename:
                cur_filename = loc["filename"]
                s.append(cur_filename + ":")
            s[-1] += f'({loc["lineno"]},{loc["col"]},{loc["span_col"]})'
        return f"<{';'.join(s)}>"
