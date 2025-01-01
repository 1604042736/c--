from Basic import Location, Token


class Node:
    """语法树节点"""

    location: Location  # 语法树对应代码的位置
    _fields: tuple[str] = tuple()  # 子节点名称
    _attributes: tuple[str] = ("location",)  # 节点属性

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

    def accept(self, visitor, *args, **kwargs):
        for cls in self.__class__.__mro__:
            method = getattr(visitor, f"visit_{cls.__name__}", None)
            if method == None:
                continue
            method(self, *args, **kwargs)
            break


class Attribute(Node):
    prefix_name: str
    name: str
    args: list[Token]

    _attributes = Node._attributes + ("prefix_name", "name", "args")


class DeprecatedAttr(Attribute):
    pass


class MaybeUnusedAttr(Attribute):
    pass


class NoReturnAttr(Attribute):
    pass


class UnsequencedAttr(Attribute):
    pass


class FallthroughAttr(Attribute):
    pass


class NodiscardAttr(Attribute):
    pass


class ReproducibleAttr(Attribute):
    pass


class AttributeSpecifier(Node):
    attributes: list[Attribute]

    _fields = Node._fields + ("attributes",)


class TranslationUnit(Node):
    body: list[Node]

    _fields = Node._fields + ("body",)
