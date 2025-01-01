from Common import *


def test_jump_statement():
    parser = get_parser("jump_statement.txt")
    parser.nexttoken()
    for i in (
        GotoStmt(name="A"),
        ContinueStmt(),
        BreakStmt(),
        ReturnStmt(),
        ReturnStmt(expr=IntegerLiteral(value="1")),
    ):
        a = parser.jump_statement()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END


def test_iteration_statement():
    parser = get_parser("iteration_statement.txt")
    parser.nexttoken()
    for i in (
        WhileStmt(
            condition_expr=IntegerLiteral(value="1"),
            body=ExpressionStmt(expr=Reference(name="a")),
        ),
        DoWhileStmt(
            condition_expr=IntegerLiteral(value="1"),
            body=ExpressionStmt(expr=Reference(name="a")),
        ),
        ForStmt(
            init_expr=BinaryOperator(
                op=BinOpKind.ASSIGN,
                left=Reference(name="i"),
                right=IntegerLiteral(value="0"),
            ),
            body=ExpressionStmt(expr=Reference(name="a")),
        ),
        ForStmt(
            condition_expr=BinaryOperator(
                op=BinOpKind.LT,
                left=Reference(name="i"),
                right=IntegerLiteral(value="1"),
            ),
            body=ExpressionStmt(expr=Reference(name="a")),
        ),
        ForStmt(
            increase_expr=UnaryOperator(
                op=UnaryOpKind.POSTFIX_INC, operand=Reference(name="i")
            ),
            body=ExpressionStmt(expr=Reference(name="a")),
        ),
        ForStmt(
            init_expr=BinaryOperator(
                op=BinOpKind.ASSIGN,
                left=Reference(name="i"),
                right=IntegerLiteral(value="0"),
            ),
            condition_expr=BinaryOperator(
                op=BinOpKind.LT,
                left=Reference(name="i"),
                right=IntegerLiteral(value="1"),
            ),
            increase_expr=UnaryOperator(
                op=UnaryOpKind.POSTFIX_INC, operand=Reference(name="i")
            ),
            body=ExpressionStmt(),  # 顺便测试expression_stmt
        ),
        ForStmt(
            init_decl=DeclStmt(
                specifiers=[BasicTypeSpecifier(specifier_name="int")],
                declarators=[
                    TypeOrVarDecl(
                        declarator=NameDeclarator(name="i"),
                        initializer=IntegerLiteral(value="0"),
                    )
                ],
            ),
            condition_expr=BinaryOperator(
                op=BinOpKind.LT,
                left=Reference(name="i"),
                right=IntegerLiteral(value="1"),
            ),
            increase_expr=UnaryOperator(
                op=UnaryOpKind.POSTFIX_INC, operand=Reference(name="i")
            ),
            body=ExpressionStmt(expr=Reference(name="a")),
        ),
    ):
        a = parser.iteration_statement()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END


def test_selection_statement():
    parser = get_parser("selection_statement.txt")
    parser.nexttoken()
    for i in (
        IfStmt(
            condition_expr=Reference(name="a"),
            body=ExpressionStmt(expr=Reference(name="b")),
        ),
        IfStmt(
            condition_expr=Reference(name="a"),
            body=ExpressionStmt(expr=Reference(name="b")),
            else_body=ExpressionStmt(expr=Reference(name="c")),
        ),
        SwitchStmt(
            condition_expr=Reference(name="a"),
            body=CompoundStmt(
                items=[  # 顺便测试label_statement和compound_stmt
                    CaseStmt(expr=IntegerLiteral(value="1")),
                    GotoStmt(name="A"),
                    LabelStmt(name="A"),
                    DefaultStmt(),
                    ExpressionStmt(),
                ]
            ),
        ),
    ):
        a = parser.selection_statement()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END
