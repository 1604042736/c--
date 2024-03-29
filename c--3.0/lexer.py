import re
from exception import SyntaxException


class Token:
    '''
    存储token
    '''

    def __init__(self, name, lineno, linepos, filename, type=None):
        self.name = name  # token内容
        self.lineno, self.linepos = lineno, linepos  # token行列
        self.filename = filename
        self.type = type if type else name  # 类型

    def __eq__(self, other):
        return self.name == other or self.type == other

    def __str__(self):
        return f'Token(file="{self.filename}",name="{self.name}",lineno={self.lineno},linepos={self.linepos},type={self.type})'

    def __hash__(self) -> int:
        return str.__hash__(self.name)
    __repr__ = __str__


class Lexer:
    '''
    词法分析器
    '''
    pattern = '|'.join([r'([a-zA-Z]|_)([a-zA-Z]|[0-9]|_)+',  # 标识符
                       r'[0-9]+\.[0-9]+',  # 小数
                        r'[0-9]+',  # 整数
                        r'>=|<=|>|<|==|!=',  # 长度大于1的符号
                        r"'.+'|\".+\"",  # 字符串
                        r'( |\t)+',  # 缩进
                        r'.+?',  # 匹配剩余字符
                        ])

    def __init__(self, lines, filename, startlineno=0, endlineno=-1):
        self.lines = lines  # 以行为单位的代码
        self.filename = filename
        self.lineno = startlineno  # 行(开始)
        self.endlineno = endlineno if endlineno != -1 else len(lines)  # 结束位置
        self.tokens = None  # 当前行所有的token
        self.tokenindex = 0  # 索引
        self.eof = False  # 代码是否结束
        self.token = None
        self.indent = ''  # 当前缩进

        self.set_tokens()
        self.get_token()

    def get_token(self):
        '''
        获取一个token
        '''
        if self.tokenindex < len(self.tokens):
            self.token = self.tokens[self.tokenindex]
            self.tokenindex += 1
        else:
            self.token = self.updata_tokens()
        if self.token == None:
            self.token = Token(name='<None>', lineno=self.lineno,
                               linepos=0, filename=self.filename)
        return self.token

    def updata_tokens(self):
        '''
        更新self.tokens
        '''
        if (self.lineno+1) < len(self.lines):
            self.lineno += 1
            self.set_tokens()
            return self.get_token()
        else:
            self.eof = True
            return None

    def set_tokens(self):
        '''
        设置token列表
        '''
        self.tokens = []
        self.tokenindex = 0
        if self.lineno >= self.endlineno:
            self.eof = True
            return
        line = self.lines[self.lineno]
        # 去除空行
        while (self.lineno+1) < self.endlineno and self.is_emptyline(line):
            self.lineno += 1
            line = self.lines[self.lineno]
        if self.is_emptyline(line):  # 最后一行
            return
        self.indent = self.get_indent(self.lines[self.lineno])
        for token in re.finditer(self.pattern, self.lines[self.lineno]):
            if not self.is_whitespace(token.group()):
                self.tokens.append(Token(token.group(), self.lineno, token.span()[
                                   1], self.filename))

    def get_indent(self, s):
        '''
        获取缩进
        '''
        indent = ''
        for i in s:
            if i not in (' ', '\t'):
                break
            indent += i
        return indent

    def is_emptyline(self, s):
        '''
        判断是否是空行
        '''
        for i in s:
            if i not in (' ', '\t', '\n'):
                return False
        return True

    def is_whitespace(self, s):
        '''
        判断是否全为空白字符
        '''
        for i in s:
            if i not in (' ', '\t', '\n'):
                return False
        return True

    def expect(self, expected):
        if expected not in (self.token.name, self.token.type):
            raise SyntaxException(
                self.filename, self.lines[self.lineno], self.lineno, f'期望得到{expected},实际得到{self.token}')
        return self.get_token()

    def skip_block(self):
        '''
        跳过代码块
        '''
        startline = self.lineno
        indent = self.get_indent(self.lines[self.lineno])  # 获取当前缩进
        self.lineno += 1
        # print(self.lines,self.lineno)
        while (self.lineno) < self.endlineno and indent in self.get_indent(self.lines[self.lineno]):
            self.lineno += 1
        endline = self.lineno
        #print(startline, endline, indent)
        self.set_tokens()
        self.get_token()
        return startline, endline, indent

    def __str__(self):
        return f'Lexer(filename="{self.filename}",lines={self.lines})'

    __repr__ = __str__
