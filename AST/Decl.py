from enum import Enum
from typing import TYPE_CHECKING
from AST.Node import Node, AttributeSpecifier
from AST.Stmt import Stmt

if TYPE_CHECKING:
    from AST.Expr import Expr


class Declaration(Node):
    attribute_specifiers: list[AttributeSpecifier]
    specifiers: list["SpecifierOrQualifier"]
    specifier_attributes: list[AttributeSpecifier]  # 跟在说明符后面的可选的属性列表
    declarators: list["Declarator"]

    _fields = Node._fields + (
        "attribute_specifiers",
        "specifiers",
        "specifier_attributes",
        "declarators",
    )


class DeclStmt(Stmt, Declaration):
    """声明语句"""

    _fields = Stmt._fields + Declaration._fields


class SpecifierOrQualifier(Node):
    pass


class StorageClassSpecifier(Enum):
    AUTO = "auto"
    CONSTEXPR = "contexpr"
    EXTERN = "extern"
    REGISTER = "register"
    STATIC = "static"
    THREAD_LOCAL = "thread_local"
    TYPEDEF = "typedef"


class StorageClass(SpecifierOrQualifier):
    specifier: StorageClassSpecifier

    _attributes = SpecifierOrQualifier._attributes + ("specifier",)


class Declarator(Node):
    declarator: "Declarator"
    attribute_specifiers: list[AttributeSpecifier]

    _fields = Node._fields + ("declarator", "attribute_specifiers")


class TypeOrVarDecl(Declarator):
    initializer: "Expr"

    _fields = Declarator._fields + ("initializer",)


class PointerDeclarator(Declarator):
    qualifiers: list["TypeQualifier"]

    _fields = Declarator._fields + ("qualifiers",)


class ArrayDeclarator(Declarator):
    qualifiers: list["TypeQualifier"]
    size: "Expr"
    is_star_modified: bool
    is_static: bool

    attribute = Declarator._attributes + ("is_star_modified", "is_static")
    _fields = Declarator._fields + ("qualifiers", "size")


class FunctionDeclarator(Declarator):
    parameters: list["ParamDecl"]
    has_varparam: bool

    _attributes = Declarator._attributes + ("has_varparam",)
    _fields = Declarator._fields + ("parameters",)


class NameDeclarator(Declarator):
    name: str

    _attributes = Declarator._attributes + ("name",)


class BasicTypeSpecifier(SpecifierOrQualifier):
    specifier_name: str

    _attributes = SpecifierOrQualifier._attributes + ("specifier_name",)


class BitIntSpecifier(SpecifierOrQualifier):
    size: "Expr"

    _fields = SpecifierOrQualifier._fields + ("size",)


class AtomicSpecifier(SpecifierOrQualifier):
    type_name: "TypeName"

    _fields = SpecifierOrQualifier._fields + ("type_name",)


class TypeOfSpecifier(SpecifierOrQualifier):
    arg: Node

    _fields = SpecifierOrQualifier._fields + ("arg",)


class TypeQualifier(SpecifierOrQualifier):
    qualifier_name: str

    _attributes = SpecifierOrQualifier._attributes + ("qualifier_name",)


class FunctionSpecifier(SpecifierOrQualifier):
    specifier_name: str

    _attributes = SpecifierOrQualifier._attributes + ("specifier_name",)


class TypedefSpecifier(SpecifierOrQualifier):
    specifier_name: str

    _attributes = SpecifierOrQualifier._attributes + ("specifier_name",)


class AlignSepcifier(SpecifierOrQualifier):
    type_or_expr: Node

    _attributes = SpecifierOrQualifier._attributes + ("type_or_expr",)


class RecordDecl(SpecifierOrQualifier):
    struct_or_union: str
    attribute_specifiers: list[AttributeSpecifier]
    name: str
    members_declaration: list[Node]

    _attributes = SpecifierOrQualifier._attributes + ("struct_or_union", "name")
    _fields = SpecifierOrQualifier._fields + (
        "attribute_specifiers",
        "members_declaration",
    )


class FieldDecl(Declaration):
    pass


class MemberDecl(Declarator):
    bit_field: "Expr"

    _fields = Declarator._fields + ("bit_field",)


class Enumerator(Node):
    name: str
    attribute_specifiers: list[AttributeSpecifier]
    value: "Expr"

    _attributes = Node._attributes + ("name",)
    _fields = Node._fields + (
        "attribute_specifiers",
        "value",
    )


class EnumDecl(SpecifierOrQualifier):
    attribute_specifiers: list[AttributeSpecifier]
    name: str
    specifiers: list[SpecifierOrQualifier]
    enumerators: list[Enumerator]

    _attributes = SpecifierOrQualifier._attributes + ("name",)
    _fields = SpecifierOrQualifier._fields + (
        "attribute_specifiers",
        "specifiers",
        "enumerators",
    )


class ParamDecl(Declaration):
    declarator: Declarator

    @property
    def declarators(self):
        return [self.declarator]

    _fields = list(Declaration._fields)
    _fields.remove("declarators")
    _fields = tuple(_fields) + ("declarator",)


class TypeName(Declaration):
    declarator: Declarator

    @property
    def declarators(self):
        return [self.declarator]

    _fields = list(Declaration._fields)
    _fields.remove("declarators")
    _fields = tuple(_fields) + ("declarator",)


class FunctionDef(Declaration):
    declarator: Declarator
    body: Stmt

    @property
    def declarators(self):
        return [self.declarator]

    _fields = list(Declaration._fields)
    _fields.remove("declarators")
    _fields = tuple(_fields) + ("declarator", "body")
