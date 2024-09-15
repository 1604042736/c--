from typing import Optional
from copy import deepcopy
from Basic import TokenKind, Token, Error, Location
from Lex.Lexer import Lexer
from Lex.ConcatReader import ConcatReader


class Macro:
    """宏"""

    def __init__(
        self, name: str, params: Optional[list[Token]], replacement: list[Token]
    ):
        self.name = name
        self.params = params  # 参数
        self.replacement = replacement  # 替换列表

    def __eq__(self, other: "Macro"):
        return (self.name, self.params, self.replacement) == (
            other.name,
            other.params,
            other.replacement,
        )

    def __repr__(self):
        return f"Macro('{self.name}',{self.params},{self.replacement})"

    def isObjectLike(self):
        """是否是object-like宏"""
        return self.params == None

    def hasVarParam(self):
        """是否含有变长参数"""
        return (
            self.params != None
            and len(self.params) >= 1
            and self.params[-1].kind == TokenKind.ELLIPSIS
        )

    def paramIndex(self, name) -> int:
        """返回name在参数中的索引"""
        if self.params == None:
            return -1
        for i, p in enumerate(self.params):
            if p.text == name:
                return i
        return -1

    def replace(self, args: list["MacroArg"]) -> list[Token]:
        """进行宏替换, 返回替换后的结果"""

        def get_arg(token: Token):
            # __VA_ARGS__对应的参数可能有3种情况:
            # 1. 不存在(None)
            # 2. 空列表
            # 3. 非空列表
            if token.kind != TokenKind.IDENTIFIER and not isvaargs(token):
                return None
            name = token.text
            if name == "__VA_ARGS__":
                if not self.hasVarParam():
                    raise Error(f'宏"{self.name}"没有变长参数', token.location)
                if len(args) > len(self.params) - 1:  # 存在__VA_ARGS__
                    return args[-1]
                else:
                    return None
            index = self.paramIndex(name)
            if index == -1:
                return None
            if index < len(args):
                return args[index]
            return MacroArg([], "")

        isvaargs = lambda tk: tk.kind == TokenKind.__VA_ARGS__
        isvaopt = lambda tk: tk.kind == TokenKind.__VA_OPT__

        replacement = deepcopy(self.replacement)
        new: list[Token] = []
        stringizing_num: int = 0  # 标记字符串化的数量
        i = 0
        while i < len(replacement):
            token = replacement[i]
            if isinstance(token, (StringizingStart, StringizingEnd)):
                new.append(token)
                i += 1
                continue
            arg = get_arg(token)
            if arg != None:
                i += 1
                if arg.tokens:
                    new.extend(arg.tokens)
                else:
                    new.append(PlaceMarker(token.location))
                continue
            elif isvaargs(token):
                i += 1
                continue
            elif isvaopt(token):
                if not self.hasVarParam():
                    raise Error(f'宏"{self.name}"没有变长参数', token.location)
                a = i  # __VA_OPT__出现的位置
                i += 1
                if i >= len(replacement) or replacement[i].kind != TokenKind.L_PAREN:
                    raise Error("__VA_OPT__后缺少'('", replacement[i - 1].location)
                i += 1
                paren = 1
                opt = []  # __VA_OPT__的内容
                while i < len(replacement):
                    token = replacement[i]
                    if token.kind == TokenKind.L_PAREN:
                        paren += 1
                    elif token.kind == TokenKind.R_PAREN:
                        paren -= 1
                        if paren == 0:
                            break
                    elif isvaopt(token):
                        raise Error("__VA_OPT__不能嵌套", token.location)
                    opt.append(token)
                    i += 1
                if i >= len(replacement) or token.kind != TokenKind.R_PAREN:
                    raise Error(
                        "__VA_OPT__后缺少')'",
                        replacement[i if i < len(replacement) else -1],
                    )
                i += 1  # __VA_OPT__结束的位置 ')'后
                if not (len(args) > len(self.params) - 1 and args[-1].tokens):
                    opt = []
                replacement[a:i] = opt
                if stringizing_num:
                    stringizing_num -= 1
                    replacement.insert(a + len(opt), StringizingEnd())
                i = a
                continue
            elif token.kind == TokenKind.HASH and not self.isObjectLike():
                token = replacement[i + 1]
                arg = get_arg(token)
                if arg == None and isvaargs(token):
                    text = ""
                elif arg == None and isvaopt(token):
                    new.append(StringizingStart(token.location))
                    stringizing_num += 1
                    i += 1
                    continue
                elif arg == None:
                    raise Error(
                        f"'#'后面应该跟一个参数而不是'{token.text}'", token.location
                    )
                else:
                    text = arg.text
                token = Token(
                    TokenKind.STRINGLITERAL,
                    token.location,
                    '"' + text.replace('"', '\\"') + '"',
                )
                i += 1
            elif token.kind == TokenKind.HASHHASH:
                new.append(ConcatMarker(token.location))
                i += 1
                continue
            new.append(token)
            i += 1

        def handle_concatmarker(i):
            if i == 0 or i == len(new) - 1:
                raise Error("'##'不应该出现在替换列表的开头或结尾", new[i].location)
            # 确定需要连接的token和需要进行替换的位置
            tokens = []
            start, end = i, i + 1
            a = new[i - 1]
            b = new[i + 1]
            if not isinstance(
                a, (StringizingStart, ConcatMarker, StringizingEnd, PlaceMarker)
            ):
                tokens.append(a)
                start = i - 1
            if not isinstance(
                b, (StringizingStart, ConcatMarker, StringizingEnd, PlaceMarker)
            ):
                tokens.append(b)
                end = i + 2
            if isinstance(a, PlaceMarker):
                start = i - 1
            if isinstance(b, PlaceMarker):
                end = i + 2
            if not tokens:
                new[start:end] = [PlaceMarker(new[i].location)]
                return
            reader = ConcatReader(tokens)
            lexer = Lexer(reader)
            token = lexer.next()
            while token.kind != TokenKind.END:
                token = lexer.next()
            new[start:end] = lexer.tokens[:-1]

        i = 0
        while i < len(new):
            if isinstance(new[i], StringizingStart):
                j = i + 1
                while j < len(new) and not isinstance(new[j], StringizingEnd):
                    if isinstance(new[j], ConcatMarker):
                        handle_concatmarker(j)
                        j -= 1
                    j += 1
                location = Location(new[i].location)
                text = []
                for k in range(i + 1, j):
                    if isinstance(new[k], PlaceMarker):
                        continue
                    text.append(new[k].text)
                    location.extend(new[k].location)
                text = " ".join(text)
                new[i : j + 1] = [
                    Token(
                        TokenKind.STRINGLITERAL,
                        location,
                        '"' + text.replace('"', '\\"') + '"',
                    )
                ]
            elif isinstance(new[i], ConcatMarker):
                handle_concatmarker(i)
                i -= 1
            i += 1
        i = 0
        while i < len(new):
            if isinstance(new[i], PlaceMarker):
                new.pop(i)
                i -= 1
            i += 1
        return new


class MacroArg:
    """宏替换的实参"""

    def __init__(self, tokens: list[Token], text: str) -> None:
        self.tokens: list[Token] = tokens
        self.text = text  # 这些实参对应的文本

    def __repr__(self):
        return f"MacroArg({self.tokens},'{self.text}')"


class StringizingStart:
    """'#'的开始标记(__VA_OPT__)"""

    def __init__(self, location: Location):
        self.location = location


class StringizingEnd:
    pass


class PlaceMarker:
    def __init__(self, location: Location):
        self.location = location


class ConcatMarker:
    """'##' 运算的标记"""

    def __init__(self, location: Location) -> None:
        self.location = location
