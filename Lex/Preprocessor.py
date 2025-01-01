import os
import datetime
from enum import Enum
from typing import Optional
from Basic import Diagnostic, Error, Token, TokenKind, FileReader, DiagnosticKind
from Lex.Lexer import Lexer
from Lex.Macro import Macro, MacroArg


class PPState(Enum):
    """预处理器状态"""

    HANDLINGDIRECTIVE = "HandlingDirective"  # 正在处理预处理器指令
    GETTINGMACROARGS = "GettingMacroArgs"  # 正在获取宏替换参数
    IGNORECOMMENT = "IgnoreComment"  # 忽略注释
    SKIPPINGGROUP = "SkippingGroup"  # 正在跳过组
    HANDLINGINCLUDE = "HandlingInclude"  # 处理include指令
    HANDLINGLINE = "HandlingLine"
    HANDLINGEMBED = "HandlingEmbed"


class Preprocessor(Lexer):
    include_path: list[str] = []  # 包含文件查找路径

    def __init__(self, reader: FileReader):
        super().__init__(reader)
        self.macros: dict[str, Macro] = {}
        self.state: list[PPState] = [
            PPState.IGNORECOMMENT
        ]  # 正在处理的预处理指令, 没在处理时为None
        self.condpp_val: list[bool] = []  # 条件预处理指令的结果
        self.headerpp: list[Preprocessor] = []  # 包含的文件的预处理器
        self.filename = self.reader.filename  # 用于 __FILE__ 替换
        self.line_shift = 0  # 用于 __LINE__ 替换时进行调整

    def check_pphash(self):
        """判断当前读到的'#'是否算是预处理器指令"""
        i = self.nextindex - 2
        atbegineofline = True  # 位于行首
        while i >= 0:
            if self.hasread[i][0] == "\n":
                break
            if not self.hasread[i][0].isspace():
                atbegineofline = False
                break
            i -= 1
        return atbegineofline

    def next(self):
        token = super().next()

        if (
            PPState.SKIPPINGGROUP not in self.state
            and token.kind == TokenKind.HASH
            and token.ispphash
        ):
            self.handleDirective()
            return self.next()

        # 尝试进行宏替换
        if (
            (
                PPState.HANDLINGDIRECTIVE not in self.state
                or PPState.HANDLINGINCLUDE in self.state
                or PPState.HANDLINGLINE in self.state
                or PPState.HANDLINGEMBED in self.state
            )
            and PPState.GETTINGMACROARGS not in self.state
            and token.kind == TokenKind.IDENTIFIER
        ):
            if self.replaceMacro():  # 进行了替换
                return self.next()

        # 连接相邻的字符串字面量
        while (
            all([i == PPState.IGNORECOMMENT for i in self.state])
            and token.kind == TokenKind.STRINGLITERAL
        ):
            t = self.save()
            token2 = super().next()
            if token2.kind == TokenKind.STRINGLITERAL:
                token.text += " " + token2.text
                token.content += token2.content
                token.location.extend(token2.location)
                prefix_index = ["", "u8", "L", "u", "U"]
                token.prefix = prefix_index[
                    max(
                        prefix_index.index(token.prefix),
                        prefix_index.index(token2.prefix),
                    )
                ]
                self.nexttk_index -= 1
                self.tokens.pop(self.nexttk_index)
            else:
                self.restore(t)
                break
        return token

    def getNewToken(self) -> Token:
        if self.headerpp:
            token = self.headerpp[-1].next()
            if token.kind == TokenKind.END:
                self.headerpp.pop()
                return None
            return token
        ch, location = self.getch()
        if ch == "/":
            ch, loc = self.getch()
            location.extend(loc)
            if ch == "/":
                text = ""
                ch, loc = self.getch()
                while ch and ch != "\n":
                    text += ch
                    location.extend(loc)
                    ch, loc = self.getch()
                return (
                    Token(TokenKind.COMMENT, location, text)
                    if PPState.IGNORECOMMENT not in self.state
                    else None
                )
            elif ch == "*":
                text = ""
                ch, loc = self.getch()
                while ch and text[-2:] != "*/":
                    text += ch
                    location.extend(loc)
                    ch, loc = self.getch()
                self.ungetch()
                return (
                    Token(TokenKind.COMMENT, location, text[:-2])
                    if PPState.IGNORECOMMENT not in self.state
                    else None
                )
            else:
                # 多读了两个
                self.ungetch()
                self.ungetch()
        elif ch == "\n" and PPState.HANDLINGDIRECTIVE in self.state:
            return Token(TokenKind.NEWLINE, location, ch)
        elif ch == "<" and PPState.HANDLINGINCLUDE in self.state:
            text = ""
            ch, loc = self.getch()
            while ch and ch != ">":
                text += ch
                location.extend(loc)
                ch, loc = self.getch()
            return Token(TokenKind.HEADERNAME, location, text)
        else:
            self.ungetch()
        token = super().getNewToken()
        if token != None:
            if token.kind == TokenKind.IDENTIFIER:
                token.kind = Token.ppkeywords.get(token.text, TokenKind.IDENTIFIER)
            elif token.kind == TokenKind.HASH:
                token.ispphash = self.check_pphash()
        return token

    def handleDirective(self) -> list[Token]:
        """处理预处理指令并返回新的token序列"""

        def read_until_line_end():
            """一直读到行末"""
            while self.curtoken().kind not in (TokenKind.NEWLINE, TokenKind.END):
                self.next()

        self.state.append(PPState.HANDLINGDIRECTIVE)
        start = self.nexttk_index - 1

        token = self.next()
        if token.kind == TokenKind.DEFINE:
            self.handleDefine()
            read_until_line_end()
        elif token.kind == TokenKind.UNDEF:
            token = self.next()
            if token.kind != TokenKind.IDENTIFIER:
                raise Error("宏名应该是个标识符", token.location)
            if token.text in self.macros:
                self.macros.pop(token.text)
            read_until_line_end()
        elif token.kind in (TokenKind.IFDEF, TokenKind.IFNDEF):
            reverse = token.kind == TokenKind.IFNDEF  # 是否需要将结果反转
            token = self.next()
            if token.kind != TokenKind.IDENTIFIER:
                raise Error("宏名应该是个标识符", token.location)
            val = token.text in self.macros  # 表达式的值
            if reverse:
                val = not val
            self.condpp_val.append(val)
            if val:  # 条件成立
                read_until_line_end()
            else:
                self.skipGroup()
        elif token.kind in (TokenKind.ELIFDEF, TokenKind.ELIFNDEF):
            reverse = token.kind == TokenKind.ELIFNDEF
            token = self.next()
            if token.kind != TokenKind.IDENTIFIER:
                raise Error("宏名应该是个标识符", token.location)
            if self.condpp_val[-1] == True:
                self.skipGroup()
            else:
                val = token.text in self.macros  # 表达式的值
                if reverse:
                    val = not val
                self.condpp_val[-1] = val
                if val:  # 条件成立
                    read_until_line_end()
                else:
                    self.skipGroup()
        elif token.kind == TokenKind.IF:
            read_until_line_end()  # TODO:
        elif token.kind == TokenKind.ELIF:
            read_until_line_end()  # TODO:
        elif token.kind == TokenKind.ENDIF:
            self.condpp_val.pop()
        elif token.kind == TokenKind.INCLUDE:
            self.state.append(PPState.HANDLINGINCLUDE)

            token = self.next()
            include_path = self.include_path
            if token.kind == TokenKind.HEADERNAME:
                pass
            elif token.kind == TokenKind.STRINGLITERAL:
                include_path = ["."] + include_path
            else:
                raise Error('期望得到<FILENAME>或者"FILENAME"', token.location)
            pp = self.include(token.text, include_path)
            if pp == None:
                raise Error(f"无法包含文件: {token.text}", token.location)
            read_until_line_end()
            self.headerpp.append(pp)

            self.state.pop()
        elif token.kind == TokenKind.EMBED:
            read_until_line_end()  # TODO:
        elif token.kind in (TokenKind.ERROR, TokenKind.WARNING):
            text = ""
            ch, _ = self.getch()
            while ch and ch != "\n":
                text += ch
                ch, _ = self.getch()
            if token.kind == TokenKind.ERROR:
                raise Error(text.strip(), token.location)
            elif token.kind == TokenKind.WARNING:
                Diagnostic(text.strip(), token.location, DiagnosticKind.WARNING).dump()
        elif token.kind == TokenKind.LINE:
            self.state.append(PPState.HANDLINGLINE)
            token = self.next()
            if token.kind != TokenKind.INTCONST:
                raise Error("#line期望得到一个整数")
            val = int(token.text)
            self.line_shift = val - token.location[0]["lineno"]

            token = self.next()
            if token.kind == TokenKind.STRINGLITERAL:
                self.filename = token.text

            self.state.pop()
            read_until_line_end()
        elif token.kind == TokenKind.PRAGMA:
            read_until_line_end()
        elif token.kind not in (TokenKind.NEWLINE, TokenKind.END):
            raise Error("未知的预处理器参数", token.location)
        else:
            read_until_line_end()

        end = self.nexttk_index
        self.tokens[start:end] = []
        self.nexttk_index = start

        self.state.pop()

    def handleDefine(self):
        """处理define指令"""
        token = self.next()
        if token.kind != TokenKind.IDENTIFIER:
            raise Error("宏名应该是个标识符", token.location)
        name_tk = token  # 用于后面处理错误
        name = token.text
        params: Optional[list[Token]] = None  # 参数列表
        replacement: list[Token] = []  # 替换列表

        ch, _ = self.getch()
        if ch == "(":  # 参数列表
            params = []
            token = self.next()
            while token.kind not in (TokenKind.R_PAREN, TokenKind.END):
                if token.kind not in (TokenKind.IDENTIFIER, TokenKind.ELLIPSIS):
                    raise Error("宏的参数应该是标识符或者'...'", token.location)
                params.append(token)
                token = self.next()
                if token.kind not in (TokenKind.COMMA, TokenKind.R_PAREN):
                    raise Error("宏参数应该用','分隔", token.location)
                if token.kind == TokenKind.COMMA:
                    token = self.next()
            if token.kind != TokenKind.R_PAREN:
                raise Error("宏参数列表未结束", token.location)
        else:
            self.ungetch()

        token = self.next()
        while token.kind not in (TokenKind.NEWLINE, TokenKind.END):
            replacement.append(token)
            token = self.next()

        macro = Macro(name, params, replacement)
        if name not in self.macros:
            self.macros[name] = macro
        elif self.macros[name] != macro:
            raise Error(f"重定义宏: {name}", name_tk.location)

    def replaceMacro(self):
        """宏替换, 如果发生了替换就返回True, 否则返回False"""
        name = self.curtoken().text
        if name in ("__DATE__", "__FILE__", "__LINE__", "__TIME__"):  # 预定义的宏
            if name == "__DATE__":
                token = Token(
                    TokenKind.STRINGLITERAL,
                    self.curtoken().location,
                    f'"{datetime.datetime.now().strftime("%b %d %Y")}"',
                )
            elif name == "__FILE__":
                token = Token(
                    TokenKind.STRINGLITERAL,
                    self.curtoken().location,
                    f'"{self.filename}"',
                )
            elif name == "__LINE__":
                token = Token(
                    TokenKind.INTCONST,
                    self.curtoken().location,
                    f'{self.curtoken().location[0]["lineno"]+self.line_shift}',
                )
            elif name == "__TIME__":
                token = Token(
                    TokenKind.STRINGLITERAL,
                    self.curtoken().location,
                    f'"{datetime.datetime.now().strftime("%H:%M:%S")}"',
                )
            self.tokens[self.nexttk_index - 1 : self.nexttk_index] = [token]
            self.nexttk_index -= 1
            return True
        elif name not in self.macros:
            return False
        start = self.nexttk_index - 1  # 替换开始的位置
        macro = self.macros[name]
        if macro.isObjectLike():
            replaced_token = macro.replace([])
        else:
            args = self.getMacroArgs(macro)
            if (
                args == None
                # 参数数量不匹配
                or (
                    not macro.hasVarParam()
                    and (
                        len(args) != len(macro.params)
                        and len(macro.params) != 1  # 这部分的说明在标准里没有找到
                        and len(args) != 0
                    )
                )
                or (macro.hasVarParam() and len(args) < len(macro.params) - 1)
            ):
                self.nexttk_index = start + 1
                return False
            replaced_token = macro.replace(args)
        end = self.nexttk_index  # 替换结束位置
        self.tokens[start:end] = replaced_token
        self.nexttk_index = start
        return True

    def getMacroArgs(self, macro: Macro) -> Optional[list[MacroArg]]:
        """获取宏替换的实参"""
        token = self.next()
        if token.kind != TokenKind.L_PAREN:  # 不存在实参
            return None
        self.state.append(PPState.GETTINGMACROARGS)
        token = self.next()
        args: list[MacroArg] = []
        while token.kind not in (TokenKind.R_PAREN, TokenKind.END):
            text = ""
            paren = 0
            invarparam = (
                macro.hasVarParam() and len(args) >= len(macro.params) - 1
            )  # 当前获取的是否是变长参数
            argtk_start = self.nexttk_index - 1
            while token.kind != TokenKind.END:
                if token.kind == TokenKind.COMMA and paren == 0 and not invarparam:
                    break
                elif token.kind == TokenKind.L_PAREN:
                    paren += 1
                elif token.kind == TokenKind.R_PAREN:
                    if paren == 0:
                        break
                    else:
                        paren -= 1
                if token.text != "\n":
                    text += token.text + " "
                token = self.next()

            # 对参数进行展开
            self.state.pop()
            lasttk = self.curtoken()
            self.nexttk_index = argtk_start
            token = self.next()
            while token is not lasttk:
                token = self.next()
            self.state.append(PPState.GETTINGMACROARGS)

            argtk_end = self.nexttk_index
            tokens = self.tokens[argtk_start : argtk_end - 1]
            arg = MacroArg(tokens, text.strip())
            args.append(arg)

            if token.kind == TokenKind.COMMA:
                token = self.next()
        self.state.pop()
        if token.kind != TokenKind.R_PAREN:
            return None
        return args

    def skipGroup(self):
        """用于条件预处理器跳过块"""
        self.state.append(PPState.SKIPPINGGROUP)
        level = 1
        while True:
            # 保存当前的索引信息
            token = self.next()
            if token.kind == TokenKind.HASH and token.ispphash:
                token = self.next()
                if token.kind in (TokenKind.IFDEF, TokenKind.IFNDEF, TokenKind.IF):
                    level += 1
                elif token.kind in (
                    TokenKind.ELIF,
                    TokenKind.ELIFDEF,
                    TokenKind.ELIFNDEF,
                    TokenKind.ENDIF,
                ):
                    level -= 1
                    if level == 0:
                        self.back()  # 预处理指令
                        self.back()  # '#'
                        break
            elif token.kind == TokenKind.END:
                break
        self.state.pop()

    def include(self, filename, include_path) -> "Preprocessor":
        """包含一个文件并返回这个文件的预处理器"""
        for path in include_path:
            filepath = os.path.join(path, filename)
            if not os.path.exists(filepath):
                continue
            reader = FileReader(filepath)
            pp = Preprocessor(reader)
            pp.macros = self.macros
            return pp
        return None
