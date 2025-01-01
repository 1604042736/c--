"""
各种各样的装饰器
"""

from typing import TYPE_CHECKING, Callable
from AST import Declaration, StorageClass, StorageClassSpecifier, NameDeclarator
from Basic import Diagnostic, Error, Token
from Parse.CallTree import CallTree

if TYPE_CHECKING:
    from Parse.Parser import Parser


def may_update_type_symbol(parser_method):
    """该Parser方法的返回值可能能够用来更新Parser.type_symbol"""

    def wrapper(self: "Parser", *args, **kwargs):
        node = parser_method(self, *args, **kwargs)
        if not isinstance(node, Declaration):
            return node
        for i in node.specifiers:
            if (
                isinstance(i, StorageClass)
                and i.specifier == StorageClassSpecifier.TYPEDEF
            ):
                break
        else:
            return node
        for i in node.declarators:
            a = i
            while a != None:
                if isinstance(a, NameDeclarator):
                    self.type_symbol.append(a.name)
                    break
                a = a.declarator
        return node

    return wrapper


def may_enter_scope(parser_method):
    """该Parser方法对应的语法结构可能会进入一个新的作用域"""

    def wrapper(self: "Parser", *args, **kwargs):
        type_symbol = tuple(self.type_symbol)
        ret = parser_method(self, *args, **kwargs)
        self.type_symbol = list(type_symbol)
        return ret

    return wrapper


def update_call_tree(parser_method: Callable):
    """被装饰的方法调用时将会更新Parser的调用树"""
    method_name = parser_method.__code__.co_name
    count = 1

    def wrapper(self: "Parser", *args, **kwargs):
        nonlocal count

        name = f"{method_name}#{count}"
        count += 1
        parent = self.cur_call_tree
        node = CallTree(name, parent, self.curtoken())
        if parent == None:
            self.call_tree = node
            self.cur_call_tree = self.call_tree
        else:
            node.depth = parent.depth + 1
            node.position = len(self.cur_call_tree.children)
            self.cur_call_tree.children.append(node)
        self.cur_call_tree = node

        node.args = args
        node.kwargs = kwargs
        ret = parser_method(self, *args, **kwargs)
        node.return_val = ret

        self.cur_call_tree = parent
        return ret

    return wrapper
