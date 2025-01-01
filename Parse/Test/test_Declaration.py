from Common import *


def test_simple_declaration():
    parser = get_parser("simple_declaration.txt")
    parser.nexttoken()
    for i in (
        DeclStmt(specifiers=[BasicTypeSpecifier(specifier_name="int")]),
        DeclStmt(
            specifiers=[BasicTypeSpecifier(specifier_name="int")],
            declarators=[TypeOrVarDecl(declarator=NameDeclarator(name="a"))],
        ),
        DeclStmt(
            specifiers=[BasicTypeSpecifier(specifier_name="int")],
            declarators=[
                TypeOrVarDecl(
                    declarator=PointerDeclarator(
                        qualifiers=[TypeQualifier(qualifier_name="const")],
                        declarator=PointerDeclarator(
                            declarator=NameDeclarator(name="a")
                        ),
                    )
                )
            ],
        ),
        DeclStmt(
            specifiers=[BasicTypeSpecifier(specifier_name="int")],
            declarators=[
                TypeOrVarDecl(
                    declarator=ArrayDeclarator(
                        size=IntegerLiteral(value="6"),
                        declarator=ArrayDeclarator(
                            size=IntegerLiteral(value="5"),
                            declarator=NameDeclarator(name="a"),
                        ),
                    )
                )
            ],
        ),
        DeclStmt(
            specifiers=[BasicTypeSpecifier(specifier_name="int")],
            declarators=[
                TypeOrVarDecl(
                    declarator=PointerDeclarator(
                        declarator=ArrayDeclarator(
                            size=IntegerLiteral(value="5"),
                            declarator=NameDeclarator(name="a"),
                        ),
                    )
                )
            ],
        ),
        DeclStmt(
            specifiers=[BasicTypeSpecifier(specifier_name="int")],
            declarators=[
                TypeOrVarDecl(
                    declarator=NameDeclarator(name="a"),
                    initializer=IntegerLiteral(value="1"),
                )
            ],
        ),
        DeclStmt(
            specifiers=[BasicTypeSpecifier(specifier_name="int")],
            declarators=[
                TypeOrVarDecl(
                    declarator=FunctionDeclarator(declarator=NameDeclarator(name="a"))
                )
            ],
        ),
        DeclStmt(
            specifiers=[BasicTypeSpecifier(specifier_name="int")],
            declarators=[
                TypeOrVarDecl(
                    declarator=FunctionDeclarator(
                        parameters=[
                            ParamDecl(
                                specifiers=[BasicTypeSpecifier(specifier_name="int")],
                                declarator=NameDeclarator(name="b"),
                            ),
                        ],
                    )
                )
            ],
        ),
        DeclStmt(
            specifiers=[BasicTypeSpecifier(specifier_name="int")],
            declarators=[
                TypeOrVarDecl(
                    declarator=FunctionDeclarator(
                        parameters=[
                            ParamDecl(
                                specifiers=[BasicTypeSpecifier(specifier_name="int")],
                                declarator=NameDeclarator(name="b"),
                            ),
                            ParamDecl(
                                specifiers=[BasicTypeSpecifier(specifier_name="int")],
                                declarator=NameDeclarator(name="c"),
                            ),
                        ],
                    )
                )
            ],
        ),
        DeclStmt(
            specifiers=[BasicTypeSpecifier(specifier_name="int")],
            declarators=[
                TypeOrVarDecl(
                    declarator=FunctionDeclarator(
                        parameters=[
                            ParamDecl(
                                specifiers=[BasicTypeSpecifier(specifier_name="int")],
                                declarator=NameDeclarator(name="b"),
                            ),
                        ],
                        has_varparam=True,
                    )
                )
            ],
        ),
    ):
        a = parser.declaration()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END


def test_record_declaration():
    parser = get_parser("record_declaration.txt")
    parser.nexttoken()
    for i in (
        DeclStmt(
            specifiers=[
                RecordDecl(
                    struct_or_union="struct",
                    members_declaration=[
                        FieldDecl(
                            specifiers=[BasicTypeSpecifier(specifier_name="int")],
                            declarators=[
                                MemberDecl(declarator=NameDeclarator(name="a")),
                                MemberDecl(declarator=NameDeclarator(name="b")),
                            ],
                        ),
                        FieldDecl(
                            specifiers=[BasicTypeSpecifier(specifier_name="int")],
                            declarators=[
                                MemberDecl(declarator=NameDeclarator(name="c")),
                                MemberDecl(declarator=NameDeclarator(name="d")),
                            ],
                        ),
                    ],
                )
            ],
            declarators=[TypeOrVarDecl(declarator=NameDeclarator(name="a"))],
        ),
        DeclStmt(
            specifiers=[
                RecordDecl(
                    struct_or_union="struct",
                    name="A",
                    members_declaration=[
                        FieldDecl(
                            specifiers=[BasicTypeSpecifier(specifier_name="int")],
                            declarators=[
                                MemberDecl(
                                    declarator=NameDeclarator(name="a"),
                                    bit_field=IntegerLiteral(value="3"),
                                ),
                                MemberDecl(
                                    declarator=NameDeclarator(name="b"),
                                    bit_field=IntegerLiteral(value="4"),
                                ),
                            ],
                        ),
                    ],
                )
            ],
        ),
        DeclStmt(
            specifiers=[
                RecordDecl(
                    struct_or_union="union",
                    members_declaration=[
                        FieldDecl(
                            specifiers=[BasicTypeSpecifier(specifier_name="int")],
                            declarators=[
                                MemberDecl(declarator=NameDeclarator(name="a")),
                                MemberDecl(declarator=NameDeclarator(name="b")),
                            ],
                        ),
                        FieldDecl(
                            specifiers=[BasicTypeSpecifier(specifier_name="int")],
                            declarators=[
                                MemberDecl(declarator=NameDeclarator(name="c")),
                                MemberDecl(declarator=NameDeclarator(name="d")),
                            ],
                        ),
                    ],
                )
            ],
        ),
        DeclStmt(
            specifiers=[
                RecordDecl(
                    struct_or_union="union",
                    name="A",
                    members_declaration=[
                        FieldDecl(
                            specifiers=[BasicTypeSpecifier(specifier_name="int")],
                            declarators=[
                                MemberDecl(
                                    declarator=NameDeclarator(name="a"),
                                    bit_field=IntegerLiteral(value="3"),
                                ),
                                MemberDecl(
                                    declarator=NameDeclarator(name="b"),
                                    bit_field=IntegerLiteral(value="4"),
                                ),
                            ],
                        ),
                    ],
                )
            ],
            declarators=[TypeOrVarDecl(declarator=NameDeclarator(name="b"))],
        ),
    ):
        a = parser.declaration()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END


def test_enum_declaration():
    parser = get_parser("enum_declaration.txt")
    parser.nexttoken()
    for i in (
        DeclStmt(
            specifiers=[
                EnumDecl(enumerators=[Enumerator(name="X"), Enumerator(name="Y")])
            ],
            declarators=[TypeOrVarDecl(declarator=NameDeclarator(name="a"))],
        ),
        DeclStmt(
            specifiers=[
                EnumDecl(
                    name="A", enumerators=[Enumerator(name="X"), Enumerator(name="Y")]
                )
            ],
        ),
        DeclStmt(
            specifiers=[
                EnumDecl(
                    name="A",
                    enumerators=[
                        Enumerator(name="X", value=IntegerLiteral(value="1")),
                        Enumerator(name="Y", value=IntegerLiteral(value="2")),
                    ],
                )
            ],
            declarators=[TypeOrVarDecl(declarator=NameDeclarator(name="a"))],
        ),
    ):
        a = parser.declaration()
        a.accept(DumpVisitor())
        check_ast(a, i)
    assert parser.curtoken().kind == TokenKind.END
