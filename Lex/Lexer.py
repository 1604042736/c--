from copy import deepcopy
import re
import unicodedata

from Basic import Token, TokenGen, TokenKind, Error, FileReader, Location


class Lexer(TokenGen):
    def __init__(self, reader: FileReader):
        self.reader = reader
        self.tokens: list[Token] = []  # 当前已经读到的token
        self.nexttk_index = 0  # 当前token索引
        self.hasread: list[tuple[str, Location]] = []  # 已经读到的字符
        self.nextindex = 0

    def getch(self) -> tuple[str, Location]:
        if self.nextindex >= len(self.hasread):
            char, location = self.reader.next()
            while char == "\\":
                # 凡在反斜杠出现于行尾（紧跟换行符）时，删除反斜杠和换行符，把两个物理源码行组合成一个逻辑源码行
                ch, _ = self.reader.next()
                if ch == "\n":
                    char, location = self.reader.next()
                else:
                    self.reader.back()
                    break
            self.hasread.append((char, location))
        ch, location = self.hasread[self.nextindex]
        self.nextindex += 1
        return ch, deepcopy(location)

    def ungetch(self):
        self.nextindex -= 1

    def curch(self):
        return self.hasread[self.nextindex - 1]

    def next(self):
        if self.nexttk_index >= len(self.tokens):
            token = self.getNewToken()
            while token == None:
                token = self.getNewToken()
            self.tokens.append(token)
        token = self.tokens[self.nexttk_index]
        self.nexttk_index += 1
        return token

    def back(self):
        assert self.nexttk_index > 0
        self.nexttk_index -= 1

    def save(self):
        return self.nexttk_index

    def restore(self, index):
        self.nexttk_index = index

    def getNewToken(self) -> Token:
        """获取下一个新的token"""
        ch, location = self.getch()
        if ch.isspace():  # 去除空白字符
            return None
        if ch == "":
            return Token(TokenKind.END, location, ch)
        elif self.isIdentifierStart(ch):
            text = ch
            ch, loc = self.getch()
            while ch and self.isIdentifierContinue(ch):
                text += ch
                location.extend(loc)
                ch, loc = self.getch()

            if text in ("u8", "u", "U", "L") and ch in (
                '"',
                "'",
            ):  # 字符常量或字符串字面量
                loc = location + loc
                if ch == '"':
                    return self.matchStringOrChar(
                        loc, TokenKind.STRINGLITERAL, text + ch
                    )
                elif ch == "'":
                    return self.matchStringOrChar(loc, TokenKind.CHARCONST, text + ch)
            self.ungetch()
            return Token(
                Token.keywords.get(text, TokenKind.IDENTIFIER),
                location,
                text,
            )
        elif ch == '"':
            return self.matchStringOrChar(location, TokenKind.STRINGLITERAL, ch)
        elif ch == "'":
            return self.matchStringOrChar(location, TokenKind.CHARCONST, ch)
        elif ch.isdigit():
            return self.matchDigit(location, ch)
        elif ch == ".":
            ch, loc = self.getch()
            if ch.isdigit():
                location.extend(loc)
                return self.matchDigit(location, "." + ch)
            elif ch == ".":
                ch, loc2 = self.getch()
                if ch == ".":
                    location.extend(loc + loc2)
                    return Token(TokenKind.ELLIPSIS, location, "...")
                else:
                    self.ungetch()
            self.ungetch()
            ch = self.curch()[0]  # 之前更改过ch的值
        return self.matchPunctuator(location, ch)

    def matchDigit(self, location: Location, text=""):
        """匹配数字"""
        # 获取这行的代码
        follow_loc = list(location)
        code = text
        ch, loc = self.getch()
        while ch and ch != "\n":
            code += ch
            follow_loc.extend(loc)
            ch, loc = self.getch()
        # 尝试匹配数字
        g = re.match(TokenKind.FLOATCONST.value, code)
        kind = None
        if g and g.span()[0] == 0:
            kind = TokenKind.FLOATCONST
        else:
            g = re.match(TokenKind.INTCONST.value, code)
            if g and g.span()[0] == 0:
                kind = TokenKind.INTCONST
        assert kind != None
        # 获取匹配到的文本
        text = code[g.span()[0] : g.span()[1]]
        location.extend(follow_loc[g.span()[0] : g.span()[1]])
        token = Token(kind, location, text)
        for _ in range(g.span()[1], len(code) + 1):
            self.ungetch()
        return token

    def matchStringOrChar(self, location: Location, kind: TokenKind, text=""):
        """匹配字符(串)"""
        quote = '"' if kind == TokenKind.STRINGLITERAL else "'"

        ch, loc = self.getch()
        while ch and ch != "\n":
            text += ch
            location.extend(loc)
            if ch == quote and text[-2] != "\\":
                break
            ch, loc = self.getch()
        else:
            raise Error("字符(串)未结束", location)
        if re.fullmatch(kind.value, text):
            return Token(kind, location, text)
        raise Error("非法的字符(串)", location)

    def matchPunctuator(self, location: Location, text="") -> Token:
        """根据token的正则表达式匹配punctuator"""
        token = Token(TokenKind.UNKOWN, deepcopy(location), text)
        while True:
            for kind in TokenKind:
                if kind not in Token.punctuator.values():
                    continue
                if re.fullmatch(kind.value, text):
                    break
            else:
                if len(text) > 1:
                    self.ungetch()
                break
            token = Token(kind, deepcopy(location), text)
            ch, loc = self.getch()
            if not ch:
                break
            text += ch
            location.extend(loc)
        return token

    def isIdentifierStart(self, ch: str):
        """判断字符是否可以作为标识符开头"""
        try:
            return ch == "_" or ch.isalpha() or "XID_Start" in unicodedata.name(ch)
        except:
            return False

    def isIdentifierContinue(self, ch):
        """判断字符是否可以作为标识符后继"""
        try:
            return (
                ch == "_"
                or ch.isdigit()
                or ch.isalpha()
                or "XID_Continue" in unicodedata.name(ch)
            )
        except:
            return False
