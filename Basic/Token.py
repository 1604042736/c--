from enum import Enum

from Basic.Location import Location

digit = "[0-9]"
nonzero_digit = "[1-9]"
decimal_constant = f"{nonzero_digit}('?{digit})*"
octal_digit = "[0-7]"
octal_constant = f"0('?{octal_digit})*"
hexadecimal_prefix = "(0x|0X)"
hexadecimal_digit = "[0-9a-fA-F]"
hexadecimal_digit_sequence = f"{hexadecimal_digit}('?{hexadecimal_digit})*"
hexadecimal_constant = f"({hexadecimal_prefix}{hexadecimal_digit_sequence})"
binary_prefix = "(0b|0B)"
binary_digit = "[01]"
binary_constant = f"{binary_prefix}{binary_digit}('?{binary_digit})*"
bit_precise_int_suffix = "(wb|WB)"
unsigned_suffix = "[uU]"
long_suffix = "[lL]"
long_long_suffix = "(ll|LL)"
integer_suffix = f"({unsigned_suffix}({long_long_suffix}|{bit_precise_int_suffix})|{unsigned_suffix}{long_suffix}?|({long_long_suffix}|{bit_precise_int_suffix}|{long_suffix}){unsigned_suffix}?)"
integer_constant = f"({hexadecimal_constant}|{binary_constant}|{octal_constant}|{decimal_constant}){integer_suffix}?"

floating_suffix = "(df|dd|dl|DF|DD|DL|[flFL])"
sign = "[+-]"
digit_sequence = f"({digit}('?{digit})*)"
binary_exponent_part = f"([pP]{sign}?{digit_sequence})"
hexadecimal_fractional_constant = rf"({hexadecimal_digit_sequence}?\.{hexadecimal_digit_sequence}|{hexadecimal_digit_sequence}\.)"
exponent_part = f"([eE]{sign}?{digit_sequence})"
fractional_constant = rf"({digit_sequence}?\.{digit_sequence}|{digit_sequence}\.)"
decimal_floating_constant = f"{fractional_constant}{exponent_part}?{floating_suffix}?|{digit_sequence}{exponent_part}{floating_suffix}?"
hexadecimal_floating_constant = f"({hexadecimal_prefix}{hexadecimal_fractional_constant}{binary_exponent_part}|{hexadecimal_prefix}{hexadecimal_digit_sequence}{binary_exponent_part}){floating_suffix}?"
floating_constant = f"{decimal_floating_constant}|{hexadecimal_floating_constant}"

hex_quad = f"{hexadecimal_digit}{{4}}"
universal_character_name = rf"(\\[uU]({hex_quad}){{1,2}})"

encoding_prefix = "(u8|u|U|L)"
hexadecimal_escape_sequence = rf"\\x{hexadecimal_digit}+"
octal_escape_sequence = rf"\\{octal_digit}{{1,3}}"
simple_escape_sequence = r"(\\'|\\\?|\\\\|\\a|\\b|\\f|\\n|\\r|\\t|\\v|" + r'\\")'
escape_sequence = f"{simple_escape_sequence}|{octal_escape_sequence}|{hexadecimal_escape_sequence}|{universal_character_name}"
c_char = rf"({escape_sequence}|[^'\n\\])"
c_char_sequence = f"{c_char}+"
character_constant = f"{encoding_prefix}?'{c_char_sequence}'"

s_char = rf'({escape_sequence}|[^"\n\\])'
s_char_sequence = f"({s_char}+)"
string_literal = f'{encoding_prefix}?"{s_char_sequence}?"'


class TokenKind(Enum):
    ALIGNAS = "alignas|_Alignas"
    ALIGNOF = "alignof|_Alignof"
    AUTO = "auto"
    BOOL = "bool|_Bool"
    BREAK = "break"
    CASE = "case"
    CHAR = "char"
    CONST = "const"
    CONSTEXPR = "constexpr"
    CONTINUE = "continue"
    DEFAULT = "default"
    DO = "do"
    DOUBLE = "double"
    ELSE = "else"
    ENUM = "enum"
    EXTERN = "extern"
    FALSE = "false"
    FLOAT = "float"
    FOR = "for"
    GOTO = "goto"
    IF = "if"
    INLINE = "inline"
    INT = "int"
    LONG = "long"
    NULLPTR = "nullptr"
    REGISTER = "register"
    RESTRICT = "restrict"
    RETURN = "return"
    SHORT = "short"
    SIGNED = "signed"
    SIZEOF = "sizeof"
    STATIC = "static"
    STATIC_ASSERT = "static_assert|_Static_assert"
    STRUCT = "struct"
    SWITCH = "switch"
    THREAD_LOCAL = "thread_local|_Thread_local"
    TRUE = "true"
    TYPEDEF = "typedef"
    TYPEOF = "typeof"
    TYPEOF_UNQUAL = "typeof_unqual"
    UNION = "union"
    UNSIGNED = "unsigned"
    VOID = "void"
    VOLATILE = "volatile"
    WHILE = "while"
    _ATOMIC = "_Atomic"
    _BITINT = "_BitInt"
    _COMPLEX = "_Complex"
    _DECIMAL128 = "_Decimal128"
    _DECIMAL32 = "_Decimal32"
    _DECIMAL64 = "_Decimal64"
    _GENERIC = "_Generic"
    _IMAGINARY = "_Imaginary"
    _NORETURN = "_Noreturn"

    IDENTIFIER = "_|[a-zA-Z](_|[a-zA-Z]|[0-9])*"
    INTCONST = integer_constant
    FLOATCONST = floating_constant
    CHARCONST = character_constant
    STRINGLITERAL = string_literal

    L_SQUARE = r"\["
    R_SQUARE = r"\]"
    L_PAREN = r"\("
    R_PAREN = r"\)"
    L_BRACE = r"\{"
    R_BRACE = r"\}"
    PERIOD = r"\."
    ELLIPSIS = r"\.\.\."
    AMP = "&"
    AMPAMP = "&&"
    AMPEQUAL = "&="
    STAR = r"\*"
    STAREQUAL = r"\*="
    PLUS = r"\+"
    PLUSPLUS = r"\+\+"
    PLUSEQUAL = r"\+="
    MINUS = "-"
    ARROW = "->"
    MINUSMINUS = "--"
    MINUSEQUAL = "-="
    TILDE = "~"
    EXCLAIM = "!"
    EXCLAIMEQUAL = "!="
    SLASH = "/"
    SLASHEQUAL = "/="
    PERCENT = "%"
    PERCENTEQUAL = "%="
    LESS = "<"
    LESSLESS = "<<"
    LESSEQUAL = "<="
    LESSLESSEQUAL = "<<="
    GREATER = ">"
    GREATERGREATER = ">>"
    GREATEREQUAL = ">="
    GREATERGREATEREQUAL = ">>="
    CARET = r"\^"
    CARETEQUAL = r"\^="
    PIPE = r"\|"
    PIPEPIPE = r"\|\|"
    PIPEEQUAL = r"\|="
    QUESTION = r"\?"
    COLON = ":"
    COLONCOLON = "::"
    SEMI = ";"
    EQUAL = "="
    EQUALEQUAL = "=="
    COMMA = ","
    HASH = "#"
    HASHHASH = "##"

    END = 0  # 文件结尾
    UNKOWN = 1  # 未知

    COMMENT = r"//.*?|/\*[\s\S]*?\*/"
    NEWLINE = r"\n"
    DEFINE = "define"
    __VA_ARGS__ = "__VA_ARGS__"
    __VA_OPT__ = "__VA_OPT__"
    UNDEF = "undef"
    IFDEF = "ifdef"
    IFNDEF = "ifndef"
    ELIF = "elif"
    ELIFDEF = "elifdef"
    ELIFNDEF = "elifndef"
    ENDIF = "endif"
    INCLUDE = "include"
    HEADERNAME = "<.*?>"
    LINE = "line"
    ERROR = "error"
    WARNING = "warning"
    PRAGMA = "pragma"
    EMBED = "embed"


class Token:
    keywords = {
        "alignas": TokenKind.ALIGNAS,
        "_Alignas": TokenKind.ALIGNAS,
        "alignof": TokenKind.ALIGNOF,
        "_Alignof": TokenKind.ALIGNOF,
        "auto": TokenKind.AUTO,
        "bool": TokenKind.BOOL,
        "_Bool": TokenKind.BOOL,
        "break": TokenKind.BREAK,
        "case": TokenKind.CASE,
        "char": TokenKind.CHAR,
        "const": TokenKind.CONST,
        "constexpr": TokenKind.CONSTEXPR,
        "continue": TokenKind.CONTINUE,
        "default": TokenKind.DEFAULT,
        "do": TokenKind.DO,
        "double": TokenKind.DOUBLE,
        "else": TokenKind.ELSE,
        "enum": TokenKind.ENUM,
        "extern": TokenKind.EXTERN,
        "false": TokenKind.FALSE,
        "float": TokenKind.FLOAT,
        "for": TokenKind.FOR,
        "goto": TokenKind.GOTO,
        "if": TokenKind.IF,
        "inline": TokenKind.INLINE,
        "int": TokenKind.INT,
        "long": TokenKind.LONG,
        "nullptr": TokenKind.NULLPTR,
        "register": TokenKind.REGISTER,
        "restrict": TokenKind.RESTRICT,
        "return": TokenKind.RETURN,
        "short": TokenKind.SHORT,
        "signed": TokenKind.SIGNED,
        "sizeof": TokenKind.SIZEOF,
        "static": TokenKind.STATIC,
        "static_assert": TokenKind.STATIC_ASSERT,
        "_Static_assert": TokenKind.STATIC_ASSERT,
        "struct": TokenKind.STRUCT,
        "switch": TokenKind.SWITCH,
        "thread_local": TokenKind.THREAD_LOCAL,
        "_Thread_local": TokenKind.THREAD_LOCAL,
        "true": TokenKind.TRUE,
        "typedef": TokenKind.TYPEDEF,
        "typeof": TokenKind.TYPEOF,
        "typeof_unqual": TokenKind.TYPEOF_UNQUAL,
        "union": TokenKind.UNION,
        "unsigned": TokenKind.UNSIGNED,
        "void": TokenKind.VOID,
        "volatile": TokenKind.VOLATILE,
        "while": TokenKind.WHILE,
        "_Atomic": TokenKind._ATOMIC,
        "_BitInt": TokenKind._BITINT,
        "_Complex": TokenKind._COMPLEX,
        "_Decimal128": TokenKind._DECIMAL128,
        "_Decimal32": TokenKind._DECIMAL32,
        "_Decimal64": TokenKind._DECIMAL64,
        "_Generic": TokenKind._GENERIC,
        "_Imaginary": TokenKind._IMAGINARY,
        "_Noreturn": TokenKind._NORETURN,
    }
    ppkeywords = {
        "define": TokenKind.DEFINE,
        "__VA_ARGS__": TokenKind.__VA_ARGS__,
        "__VA_OPT__": TokenKind.__VA_OPT__,
        "undef": TokenKind.UNDEF,
        "ifdef": TokenKind.IFDEF,
        "ifndef": TokenKind.IFNDEF,
        "elif": TokenKind.ELIF,
        "elifdef": TokenKind.ELIFDEF,
        "elifndef": TokenKind.ELIFNDEF,
        "endif": TokenKind.ENDIF,
        "include": TokenKind.INCLUDE,
        "line": TokenKind.LINE,
        "error": TokenKind.ERROR,
        "warning": TokenKind.WARNING,
        "pragma": TokenKind.PRAGMA,
        "embed": TokenKind.EMBED,
    }
    punctuator = {
        "[": TokenKind.L_SQUARE,
        "]": TokenKind.R_SQUARE,
        "(": TokenKind.L_PAREN,
        ")": TokenKind.R_PAREN,
        "{": TokenKind.L_BRACE,
        "}": TokenKind.R_BRACE,
        ".": TokenKind.PERIOD,
        "...": TokenKind.ELLIPSIS,
        "&": TokenKind.AMP,
        "&&": TokenKind.AMPAMP,
        "&=": TokenKind.AMPEQUAL,
        "*": TokenKind.STAR,
        "*=": TokenKind.STAREQUAL,
        "+": TokenKind.PLUS,
        "++": TokenKind.PLUSPLUS,
        "+=": TokenKind.PLUSEQUAL,
        "-": TokenKind.MINUS,
        "->": TokenKind.ARROW,
        "--": TokenKind.MINUSMINUS,
        "-=": TokenKind.MINUSEQUAL,
        "~": TokenKind.TILDE,
        "!": TokenKind.EXCLAIM,
        "!=": TokenKind.EXCLAIMEQUAL,
        "/": TokenKind.SLASH,
        "/=": TokenKind.SLASHEQUAL,
        "%": TokenKind.PERCENT,
        "%=": TokenKind.PERCENTEQUAL,
        "<": TokenKind.LESS,
        "<<": TokenKind.LESSLESS,
        "<=": TokenKind.LESSEQUAL,
        "<<=": TokenKind.LESSLESSEQUAL,
        ">": TokenKind.GREATER,
        ">>": TokenKind.GREATERGREATER,
        ">=": TokenKind.GREATEREQUAL,
        ">>=": TokenKind.GREATERGREATEREQUAL,
        "^": TokenKind.CARET,
        "^=": TokenKind.CARETEQUAL,
        "|": TokenKind.PIPE,
        "||": TokenKind.PIPEPIPE,
        "|=": TokenKind.PIPEEQUAL,
        "?": TokenKind.QUESTION,
        ":": TokenKind.COLON,
        "::": TokenKind.COLONCOLON,
        ";": TokenKind.SEMI,
        "=": TokenKind.EQUAL,
        "==": TokenKind.EQUALEQUAL,
        ",": TokenKind.COMMA,
        "#": TokenKind.HASH,
        "##": TokenKind.HASHHASH,
    }

    def __init__(self, kind: TokenKind, location: Location, text: str):
        self.kind = kind
        self.location = location
        self.text = text
        self.content = None  # 字符串内容
        self.prefix = None  # 字符串前缀
        if kind in (TokenKind.CHARCONST, TokenKind.STRINGLITERAL):
            i = self.text.find('"' if kind == TokenKind.STRINGLITERAL else "'")
            self.prefix = self.text[:i]
            self.content = self.text[i:]
            self.content = eval(self.content)
        self.ispphash = False  # 是否是预处理指令开头的'#'

    def __repr__(self):
        return f"Token({self.kind.name},{self.location},{repr(self.text)})"


class TokenGen:
    """token生成器基类"""

    def curtoken(self) -> Token:
        """获取当前token"""

    def next(self) -> Token:
        """获取下一个token"""

    def back(self):
        """回退当前token"""

    def save(self):
        """保存当前状态, 并返回一个可以用于恢复的值"""

    def restore(self):
        """接受用于恢复的值并恢复状态"""
