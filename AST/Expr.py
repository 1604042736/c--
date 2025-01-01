from enum import Enum
from typing import Any, Union
from AST.Node import Node
from AST.Decl import TypeName, StorageClass


class Expr(Node):
    """与表达式有关的节点"""

    value: Any  # 表达式的值(如果可以在编译期计算的话)
    type: Any  # 表达式的类型 TODO:
    _attributes = Node._attributes + ("type", "value")


class IntegerLiteral(Expr):
    """整数字面量"""


class FloatLiteral(Expr):
    """浮点数字面量"""


class StringLiteral(Expr):
    """字符串字面量"""

    prefix: str

    _attributes = Expr._attributes + ("prefix",)


class CharLiteral(Expr):
    """字符字面量"""

    prefix: str

    _attributes = Expr._attributes + ("prefix",)


class Reference(Expr):
    """对名字的引用"""

    name: str

    _attributes = Expr._attributes + ("name",)


class GenericAssociation(Expr):
    type_name: TypeName
    expr: Expr
    is_default: bool

    _attributes = Expr._attributes + ("is_default",)
    _fields = Expr._fields + ("type_name", "expr")


class GenericSelection(Expr):
    """_Generic表达式"""

    controling_expr: Expr
    assoc_list: list[GenericAssociation]

    _fields = Expr._fields + ("controling_expr", "assoc_list")


class ArraySubscript(Expr):
    """数组下标"""

    array: Expr
    index: Expr

    _fields = Expr._fields + ("array", "index")


class FunctionCall(Expr):
    """函数调用"""

    func: Expr
    args: list[Expr]

    _fields = Expr._fields + ("func", "args")


class Member(Expr):
    """成员"""

    target: Expr
    member_name: str  # 成员名
    is_arrow: bool  # 区分 '.'(False) 和 '->'(True)

    _attributes = Expr._attributes + ("member_name", "is_arrow")
    _fields = Expr._fields + ("target",)


class UnaryOpKind(Enum):
    """一元运算符类型"""

    POSTFIX_INC = "postfix ++"
    POSTFIX_DEC = "postfix --"
    PREFIX_INC = "prefix ++"
    PREFIX_DEC = "prefix --"
    ADDRESS = "&"
    INDIRECTION = "*"
    POSITIVE = "+"
    NEGATIVE = "-"
    INVERT = "~"
    NOT = "!"
    SIZEOF = "sizeof"
    ALIGNOF = "alignof"


class UnaryOperator(Expr):
    """一元运算符"""

    op: UnaryOpKind
    # 对于sizeof运算符, operand可能是Expr和TypeName
    operand: Union[Expr, TypeName]

    _attributes = Expr._attributes + ("op",)
    _fields = Expr._fields + ("operand",)


class CompoundLiteral(Expr):
    """组合字面量"""

    storage_class: list[StorageClass]
    type_name: TypeName
    initializer: Expr

    _fields = Expr._fields + ("storage_class", "type_name", "initializer")


class ExplicitCast(Expr):
    """显式类型转换"""

    type_name: TypeName
    expr: Expr

    _fields = Expr._fields + ("type_name", "expr")


class BinOpKind(Enum):
    """二元运算符种类"""

    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"
    LSHIFT = "<<"
    RSHIFT = ">>"
    EQ = "=="
    NEQ = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    BITAND = "&"
    BITOR = "|"
    BITXOR = "^"
    AND = "&&"
    OR = "||"
    ASSIGN = "="
    AMUL = "*="
    ADIV = "/="
    AMOD = "%="
    AADD = "+="
    ASUB = "-="
    ALSHIFT = "<<="
    ARSHIFT = ">>="
    ABITAND = "&="
    ABITXOR = "^="
    ABITOR = "|="
    COMMA = ","


class BinaryOperator(Expr):
    """二元运算符"""

    op: BinOpKind
    left: Expr
    right: Expr

    _attributes = Expr._attributes + ("op",)
    _fields = Expr._fields + ("left", "right")


class ConditionalOperator(Expr):
    """三目运算符"""

    condition_expr: Expr
    true_expr: Expr
    false_expr: Expr

    _fields = Expr._fields + ("condition_expr", "true_expr", "false_expr")


class InitList(Expr):
    initializers: list[Expr]

    _fields = Expr._fields + ("initializers",)


class Designator(Node):
    member: str
    index: Expr

    _attributes = Node._attributes + ("member",)
    _fields = Node._attributes + ("index",)


class Designation(Expr):
    designators: list[Designator]
    initializer: Expr

    _fields = Expr._fields + ("designators", "initializer")
