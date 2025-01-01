from AST.Visitor import Visitor
from AST.Node import Node


class Transformer(Visitor):
    """遍历语法树节点, 并用visit_XXX的返回值去替换或移除旧节点"""

    def visit_Node(self, node: Node):
        for field in node._fields:
            child = getattr(node, field)
            if isinstance(child, list):
                setattr(
                    node,
                    field,
                    filter(lambda a: a != None, [i.accept(self) for i in child]),
                )
            else:
                setattr(node, field, child.accept(self))
