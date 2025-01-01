from typing import Callable
from AST.Expr import BinaryOperator, UnaryOperator
from AST.Node import Node


class Visitor:
    """遍历语法树节点"""

    def generic_visit(self, node: Node, callback: Callable[[Node], None] = None):
        """
        通用访问方法
        """
        if callback == None:
            callback = lambda node: node.accept(self)
        for field in node._fields:
            child = getattr(node, field, None)
            if child == None:
                continue
            if isinstance(child, (list, tuple)):
                for i in child:
                    if i == None:
                        continue
                    callback(i)
            else:
                callback(child)

    def visit_Node(self, node: Node):
        self.generic_visit(node)


class DumpVisitor(Visitor):
    """输出语法树"""

    def visit_Node(self, node: Node, indent=0):
        print(" " * 2 * indent + node.__class__.__name__, end=" ")
        for i in node._attributes:
            if hasattr(node, i):
                print(getattr(node, i), end=" ")
            else:
                print(end="")
        print()
        self.generic_visit(node, lambda node: node.accept(self, indent + 1))
