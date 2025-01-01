from Common import *


def test_primary_expression():
    parser = get_parser("primary_expression.txt")
    parser.nexttoken()
    for i in (
        Reference(name="a"),
        StringLiteral(value="123"),
        CharLiteral(value="1"),
        IntegerLiteral(value="123"),
        FloatLiteral(value="123.5"),
        GenericSelection(
            controling_expr=Reference(name="a"),
            assoc_list=[
                GenericAssociation(
                    type_name=TypeName(
                        specifiers=[BasicTypeSpecifier(specifier_name="int")],
                    ),
                    expr=Reference(name="b"),
                ),
                GenericAssociation(
                    type_name=TypeName(
                        specifiers=[BasicTypeSpecifier(specifier_name="char")],
                    ),
                    expr=Reference(name="c"),
                ),
            ],
        ),
    ):
        a = parser.primary_expression()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END


def test_postfix_expression():
    parser = get_parser("postfix_expression.txt")
    parser.nexttoken()
    for i in (
        ArraySubscript(
            array=ArraySubscript(
                array=Reference(name="a"), index=IntegerLiteral(value="1")
            ),
            index=IntegerLiteral(value="2"),
        ),
        FunctionCall(func=Reference(name="f"), args=[]),
        FunctionCall(func=Reference(name="f"), args=[IntegerLiteral(value="1")]),
        FunctionCall(
            func=Reference(name="f"),
            args=[IntegerLiteral(value="1"), IntegerLiteral(value="2")],
        ),
        Member(target=Reference(name="b"), member_name="c", is_arrow=False),
        Member(target=Reference(name="b"), member_name="c", is_arrow=True),
        UnaryOperator(op=UnaryOpKind.POSTFIX_INC, operand=Reference(name="b")),
        UnaryOperator(op=UnaryOpKind.POSTFIX_DEC, operand=Reference(name="b")),
    ):
        a = parser.postfix_expression()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END


def test_unary_expression():
    parser = get_parser("unary_expression.txt")
    parser.nexttoken()
    for i in (
        UnaryOperator(op=UnaryOpKind.PREFIX_INC, operand=Reference(name="a")),
        UnaryOperator(op=UnaryOpKind.ADDRESS, operand=Reference(name="a")),
        UnaryOperator(op=UnaryOpKind.INDIRECTION, operand=Reference(name="a")),
        UnaryOperator(op=UnaryOpKind.POSITIVE, operand=Reference(name="a")),
        UnaryOperator(op=UnaryOpKind.NEGATIVE, operand=Reference(name="a")),
        UnaryOperator(op=UnaryOpKind.NOT, operand=Reference(name="a")),
        UnaryOperator(op=UnaryOpKind.INVERT, operand=Reference(name="a")),
        UnaryOperator(op=UnaryOpKind.SIZEOF, operand=Reference(name="a")),
        UnaryOperator(op=UnaryOpKind.SIZEOF, operand=Reference(name="a")),
        UnaryOperator(
            op=UnaryOpKind.SIZEOF,
            operand=TypeName(specifiers=[BasicTypeSpecifier(specifier_name="int")]),
        ),
        UnaryOperator(
            op=UnaryOpKind.ALIGNOF,
            operand=TypeName(specifiers=[BasicTypeSpecifier(specifier_name="int")]),
        ),
        UnaryOperator(op=UnaryOpKind.PREFIX_DEC, operand=Reference(name="a")),
    ):
        a = parser.unary_expression()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END


def test_cast_expression():
    parser = get_parser("cast_expression.txt")
    parser.nexttoken()
    for i in (
        ExplicitCast(
            type_name=TypeName(
                specifiers=[BasicTypeSpecifier(specifier_name="int")],
                declarator=PointerDeclarator(),
            ),
            expr=Reference(name="a"),
        ),
    ):
        a = parser.cast_expression()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END


def test_arithmetic_expression():
    parser = get_parser("arithmetic_expression.txt")
    parser.nexttoken()
    for i in (
        BinaryOperator(
            op=BinOpKind.RSHIFT,
            left=BinaryOperator(
                op=BinOpKind.LSHIFT,
                left=BinaryOperator(
                    op=BinOpKind.SUB,
                    left=BinaryOperator(
                        op=BinOpKind.ADD,
                        left=Reference(name="a"),
                        right=Reference(name="b"),
                    ),
                    right=BinaryOperator(
                        op=BinOpKind.MOD,
                        left=BinaryOperator(
                            op=BinOpKind.DIV,
                            left=BinaryOperator(
                                op=BinOpKind.MUL,
                                left=Reference(name="c"),
                                right=Reference(name="d"),
                            ),
                            right=Reference(name="e"),
                        ),
                        right=Reference(name="f"),
                    ),
                ),
                right=Reference(name="g"),
            ),
            right=Reference(name="h"),
        ),
    ):
        a = parser.shift_expression()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END


def test_conditional_expression():
    parser = get_parser("conditional_expression.txt")
    parser.nexttoken()
    for i in (
        ConditionalOperator(
            condition_expr=Reference(name="a"),
            true_expr=BinaryOperator(
                op=BinOpKind.ADD, left=Reference(name="b"), right=Reference(name="c")
            ),
            false_expr=ConditionalOperator(
                condition_expr=Reference(name="d"),
                true_expr=BinaryOperator(
                    op=BinOpKind.ADD,
                    left=Reference(name="e"),
                    right=Reference(name="f"),
                ),
                false_expr=Reference(name="g"),
            ),
        ),
    ):
        a = parser.conditional_expression()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END


def test_comma_operator():
    parser = get_parser("comma_operator.txt")
    parser.nexttoken()
    for i in (
        BinaryOperator(
            op=BinOpKind.COMMA,
            left=BinaryOperator(
                op=BinOpKind.ASSIGN,
                left=Reference(name="a"),
                right=BinaryOperator(
                    op=BinOpKind.ASSIGN,
                    left=Reference(name="b"),
                    right=Reference(name="c"),
                ),
            ),
            right=BinaryOperator(
                op=BinOpKind.ASSIGN,
                left=BinaryOperator(
                    op=BinOpKind.AADD,
                    left=Reference(name="d"),
                    right=Reference(name="e"),
                ),
                right=Reference(name="f"),
            ),
        ),
    ):
        a = parser.expression()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END
