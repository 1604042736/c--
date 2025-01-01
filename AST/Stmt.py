from typing import TYPE_CHECKING
from AST.Node import Node, AttributeSpecifier

if TYPE_CHECKING:
    from AST.Decl import DeclStmt
    from AST.Expr import Expr


class Stmt(Node):
    """与语句有关的语法树节点"""

    attribute_specifiers: list[AttributeSpecifier]

    _fields = Node._fields + ("attribute_specifiers",)


class AttributeDeclStmt(Stmt):
    """属性声明语句"""


class StaticAssert(Stmt):
    condition_expr: "Expr"
    message: str

    _attributes = Stmt._attributes + ("message",)
    _fields = Stmt._fields + ("condition_expr",)


class LabelStmt(Stmt):
    name: str
    stmt: Stmt

    _attributes = Stmt._attributes + ("name",)
    _fields = Stmt._fields + ("stmt",)


class CaseStmt(Stmt):
    expr: "Expr"
    stmt: Stmt

    _fields = Stmt._fields + ("expr", "stmt")


class DefaultStmt(Stmt):
    stmt: Stmt

    _fields = Stmt._fields + ("stmt",)


class CompoundStmt(Stmt):
    items: list[Stmt]

    _fields = Stmt._fields + ("items",)


class ExpressionStmt(Stmt):
    expr: "Expr"

    _fields = Stmt._fields + ("expr",)


class IfStmt(Stmt):
    condition_expr: "Expr"
    body: Stmt
    else_body: Stmt

    _fields = Stmt._fields + ("condition_expr", "body", "else_body")


class SwitchStmt(Stmt):
    condition_expr: "Expr"
    body: Stmt

    _fields = Stmt._fields + ("condition_expr", "body")


class ForStmt(Stmt):
    init_expr: "Expr"
    init_decl: "DeclStmt"
    condition_expr: "Expr"
    increase_expr: "Expr"
    body: Stmt

    _fields = Stmt._fields + (
        "init_expr",
        "init_decl",
        "condition_expr",
        "increase_expr",
        "body",
    )


class WhileStmt(Stmt):
    condition_expr: "Expr"
    body: Stmt

    _fields = Stmt._fields + ("condition_expr", "body")


class DoWhileStmt(Stmt):
    condition_expr: "Expr"
    body: Stmt

    _fields = Stmt._fields + ("condition_expr", "body")


class GotoStmt(Stmt):
    name: str

    _attributes = Stmt._attributes + ("name",)


class BreakStmt(Stmt):
    pass


class ContinueStmt(Stmt):
    pass


class ReturnStmt(Stmt):
    expr: "Expr"

    _fields = Stmt._fields + ("expr",)
