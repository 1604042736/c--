from Basic import Token, Location, FileReader


class ConcatReader(FileReader):
    """用于预处理中宏的'##'运算进行拼接操作"""

    def __init__(self, tokens: list[Token]):
        self.chars: list[tuple[str, Location]] = []
        for token in tokens:
            if not isinstance(token, Token):
                self.chars.append(token)
                continue
            for loc in token.location:
                filename = loc["filename"]
                lines = Location.lines[filename]
                row = loc["lineno"]
                col = loc["col"]
                span_col = loc["span_col"]
                for i in range(span_col):
                    self.chars.append(
                        (
                            lines[row - 1][col - 1 + i],
                            Location(
                                [
                                    {
                                        "filename": filename,
                                        "lineno": row,
                                        "col": col + i,
                                        "span_col": 1,
                                    }
                                ]
                            ),
                        )
                    )
        self.chars.append(("", self.chars[-1][1]))
        self.nextindex = 0

    def current(self) -> tuple[str, Location]:
        return self.chars[self.nextindex - 1]

    def next(self) -> tuple[str, Location]:
        """读取一个字符, 并返回这个字符和它对应的片段"""
        if self.nextindex >= len(self.chars):
            return self.chars[-1]
        ch, location = self.chars[self.nextindex]
        self.nextindex += 1
        return ch, location

    def back(self):
        """回退当前已经读到的字符, 使下一次读取时重新读到这个字符"""
        self.nextindex -= 1
