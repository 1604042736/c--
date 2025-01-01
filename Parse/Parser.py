from typing import Union
from AST import (
    Node,
    Reference,
    IntegerLiteral,
    FloatLiteral,
    StringLiteral,
    CharLiteral,
    GenericSelection,
    GenericAssociation,
    ArraySubscript,
    FunctionCall,
    Member,
    UnaryOperator,
    UnaryOpKind,
    CompoundLiteral,
    ExplicitCast,
    BinOpKind,
    BinaryOperator,
    ConditionalOperator,
    DeclStmt,
    TypeOrVarDecl,
    AttributeDeclStmt,
    StorageClass,
    StorageClassSpecifier,
    BasicTypeSpecifier,
    BitIntSpecifier,
    RecordDecl,
    FieldDecl,
    MemberDecl,
    EnumDecl,
    Enumerator,
    AtomicSpecifier,
    TypeOfSpecifier,
    TypeQualifier,
    FunctionSpecifier,
    TypedefSpecifier,
    AlignSepcifier,
    PointerDeclarator,
    ArrayDeclarator,
    FunctionDeclarator,
    Declarator,
    NameDeclarator,
    ParamDecl,
    TypeName,
    InitList,
    Designation,
    Designator,
    StaticAssert,
    Attribute,
    DeprecatedAttr,
    NoReturnAttr,
    AttributeSpecifier,
    NodiscardAttr,
    FallthroughAttr,
    MaybeUnusedAttr,
    UnsequencedAttr,
    ReproducibleAttr,
    LabelStmt,
    CaseStmt,
    DefaultStmt,
    CompoundStmt,
    ExpressionStmt,
    SwitchStmt,
    IfStmt,
    ForStmt,
    WhileStmt,
    DoWhileStmt,
    GotoStmt,
    BreakStmt,
    ReturnStmt,
    ContinueStmt,
    TranslationUnit,
    FunctionDef,
    Stmt,
)
from Basic import Diagnostic, Token, TokenGen, TokenKind, Error
from Parse.Wrapper import may_update_type_symbol, may_enter_scope, update_call_tree
from Parse.CallTree import CallTree


class Parser:
    """语法分析器"""

    def __init__(self, tokengen: TokenGen):
        self.tokengen: TokenGen = tokengen
        self.diagnostic: Diagnostic = None
        self.type_symbol: list[str] = []  # 种类为类型的符号
        self.call_tree: CallTree = None  # 调用树
        self.cur_call_tree: CallTree = self.call_tree  # 当前节点

    def save(self):
        return self.tokengen.save()

    def restore(self, *args, **kwargs):
        return self.tokengen.restore(*args, **kwargs)

    def curtoken(self):
        return self.tokengen.curtoken()

    def nexttoken(self):
        return self.tokengen.next()

    def lookahead(self, *args):
        z = self.save()
        for i in args:
            if self.curtoken().kind == i:
                self.nexttoken()
            else:
                self.restore(z)
                return False
        self.restore(z)
        return True

    @update_call_tree
    def expect(self, expected: TokenKind):
        """
        判断当前tokenkind是否与期待相等
        如果相等返回当前token, 同时读取下一个token
        否则返回None并设置诊断信息
        """
        curtk = self.curtoken()
        if curtk.kind != expected:
            self.diagnostic = Error(
                f"期待得到{expected}, 但实际得到{curtk.kind}", curtk.location
            )
            return None
        self.nexttoken()
        return curtk

    @update_call_tree
    def optional(self, func):
        z = self.save()
        if a := func():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def primary_expression(self) -> Node:
        """
        primary-expression:
            identifier
            constant
            string-literal
            ( expression )
            generic-selection
        """
        z = self.save()
        if (a := self.expect(TokenKind.IDENTIFIER)) and a.text not in self.type_symbol:
            return Reference(name=a.text, location=a.location)
        if a := self.expect(TokenKind.INTCONST):
            return IntegerLiteral(value=a.text, location=a.location)
        if a := self.expect(TokenKind.FLOATCONST):
            return FloatLiteral(value=a.text, location=a.location)
        if a := self.expect(TokenKind.CHARCONST):
            return CharLiteral(
                value=a.content,
                prefix=a.prefix,
                location=a.location,
            )
        if a := self.expect(TokenKind.STRINGLITERAL):
            return StringLiteral(
                value=a.content,
                prefix=a.prefix,
                location=a.location,
            )
        if (
            self.expect(TokenKind.L_PAREN)
            and (a := self.expression())
            and self.expect(TokenKind.R_PAREN)
        ):
            return a
        self.restore(z)
        if a := self.generic_selection():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def generic_selection(self):
        """
        generic-selection:
            _Generic ( assignment-expression , generic-assoc-list )
        """
        z = self.save()
        if (
            (a := self.expect(TokenKind._GENERIC))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.assignment_expression())
            and self.expect(TokenKind.COMMA)
            and (c := self.generic_assoc_list()) != None
            and self.expect(TokenKind.R_PAREN)
        ):
            return GenericSelection(
                controling_expr=b,
                assoc_list=c,
                location=a.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def generic_assoc_list(self) -> list[Node]:
        """
        generic-assoc-list:
            generic-association
            generic-assoc-list , generic-association
        """
        z = self.save()
        a = []
        if (b := self.generic_association()) == None:
            self.restore(z)
            return None
        a.append(b)
        z = self.save()
        while self.expect(TokenKind.COMMA) and (b := self.generic_association()):
            a.append(b)
            z = self.save()
        self.restore(z)
        return a

    @update_call_tree
    def generic_association(self):
        """
        generic-association:
            type-name : assignment-expression
            default : assignment-expression
        """
        z = self.save()
        if (
            (a := self.type_name())
            and self.expect(TokenKind.COLON)
            and (b := self.assignment_expression())
        ):
            return GenericAssociation(
                type_name=a,
                expr=b,
                is_default=False,
                location=a.location,
            )
        self.restore(z)
        if (
            (a := self.expect(TokenKind.DEFAULT))
            and self.expect(TokenKind.COLON)
            and (b := self.assignment_expression())
        ):
            return GenericAssociation(
                expr=b,
                is_default=True,
                location=a.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def postfix_expression(self):
        """
        postfix-expression:
            primary-expression
            postfix-expression [ expression ]
            postfix-expression ( argument-expression-list[opt] )
            postfix-expression . identifier
            postfix-expression -> identifier
            postfix-expression ++
            postfix-expression --
            compound-literal
        """
        z = self.save()
        if a := self.compound_literal():
            return a
        self.restore(z)
        if (a := self.primary_expression()) == None:
            self.restore(z)
            return None
        while self.curtoken().kind in (
            TokenKind.L_SQUARE,
            TokenKind.L_PAREN,
            TokenKind.PERIOD,
            TokenKind.ARROW,
            TokenKind.PLUSPLUS,
            TokenKind.MINUSMINUS,
        ):
            token = self.curtoken()
            if (
                token.kind == TokenKind.L_SQUARE
                and self.expect(TokenKind.L_SQUARE)
                and (b := self.expression())
                and self.expect(TokenKind.R_SQUARE)
            ):
                a = ArraySubscript(
                    array=a,
                    index=b,
                    location=token.location,
                )
            elif (
                token.kind == TokenKind.L_PAREN
                and self.expect(TokenKind.L_PAREN)
                and ((b := self.optional(self.argument_expression_list)),)
                and self.expect(TokenKind.R_PAREN)
            ):
                a = FunctionCall(
                    func=a,
                    args=(b if b != None else []),
                    location=token.location,
                )
            elif (
                token.kind == TokenKind.PERIOD
                and self.expect(TokenKind.PERIOD)
                and (b := self.expect(TokenKind.IDENTIFIER))
            ):
                a = Member(
                    target=a,
                    member_name=b.text,
                    is_arrow=False,
                    location=token.location,
                )
            elif (
                token.kind == TokenKind.ARROW
                and self.expect(TokenKind.ARROW)
                and (b := self.expect(TokenKind.IDENTIFIER))
            ):
                a = Member(
                    target=a,
                    member_name=b.text,
                    is_arrow=True,
                    location=token.location,
                )
            elif token.kind == TokenKind.PLUSPLUS and self.expect(TokenKind.PLUSPLUS):
                a = UnaryOperator(
                    op=UnaryOpKind.POSTFIX_INC,
                    operand=a,
                    location=token.location,
                )
            elif token.kind == TokenKind.MINUSMINUS and self.expect(
                TokenKind.MINUSMINUS
            ):
                a = UnaryOperator(
                    op=UnaryOpKind.POSTFIX_DEC,
                    operand=a,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def argument_expression_list(self) -> list[Node]:
        """
        argument-expression-list:
            assignment-expression
            argument-expression-list , assignment-expression
        """
        z = self.save()
        a = []
        if (b := self.assignment_expression()) == None:
            self.restore(z)
            return None
        a.append(b)
        while self.curtoken().kind == TokenKind.COMMA:
            if self.expect(TokenKind.COMMA) and (b := self.assignment_expression()):
                a.append(b)
            else:
                self.restore(z)
                return None
        self.restore(z)
        return a

    @update_call_tree
    def compound_literal(self):
        """
        compound-literal:
            ( storage-class-specifiers[opt] type-name ) braced-initializer
        """
        z = self.save()
        if (
            (a := self.expect(TokenKind.L_PAREN))
            and ((b := self.optional(self.storage_class_specifiers)),)
            and (c := self.type_name())
            and self.expect(TokenKind.R_PAREN)
            and (d := self.braced_initializer())
        ):
            return CompoundLiteral(
                storage_class=b,
                type_name=c,
                initializer=d,
                location=a.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def storage_class_specifiers(self) -> list[Node]:
        """
        storage-class-specifiers:
            storage-class-specifier
            storage-class-specifiers storage-class-specifier
        """
        z = self.save()
        a = []
        if (b := self.storage_class_specifier()) == None:
            self.restore(z)
            return None
        a.append(b)
        z = self.save()
        while b := self.storage_class_specifier():
            a.append(b)
            z = self.save()
        self.restore(z)
        return a

    @update_call_tree
    def unary_expression(self):
        """
        unary-expression:
            postfix-expression
            ++ unary-expression
            -- unary-expression
            unary-operator cast-expression
            sizeof unary-expression
            sizeof ( type-name )
            alignof ( type-name )
        unary-operator: one of
            & * + - ~ !
        """
        z = self.save()
        if (a := self.expect(TokenKind.PLUSPLUS)) and (b := self.unary_expression()):
            return UnaryOperator(
                op=UnaryOpKind.PREFIX_INC,
                operand=b,
                location=a.location,
            )
        self.restore(z)
        if (a := self.expect(TokenKind.MINUSMINUS)) and (b := self.unary_expression()):
            return UnaryOperator(
                op=UnaryOpKind.PREFIX_DEC,
                operand=b,
                location=a.location,
            )
        self.restore(z)

        unary_operator = {
            TokenKind.AMP: UnaryOpKind.ADDRESS,
            TokenKind.STAR: UnaryOpKind.INDIRECTION,
            TokenKind.PLUS: UnaryOpKind.POSITIVE,
            TokenKind.MINUS: UnaryOpKind.NEGATIVE,
            TokenKind.TILDE: UnaryOpKind.INVERT,
            TokenKind.EXCLAIM: UnaryOpKind.NOT,
        }
        token = self.curtoken()
        if (
            token.kind in unary_operator
            and (a := self.expect(token.kind))
            and (b := self.cast_expression())
        ):
            return UnaryOperator(
                op=unary_operator[token.kind],
                operand=b,
                location=a.location,
            )
        self.restore(z)

        if (a := self.expect(TokenKind.SIZEOF)) and (b := self.unary_expression()):
            return UnaryOperator(
                op=UnaryOpKind.SIZEOF,
                operand=b,
                location=a.location,
            )
        self.restore(z)
        if (
            (a := self.expect(TokenKind.SIZEOF))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.type_name())
            and self.expect(TokenKind.R_PAREN)
        ):
            return UnaryOperator(
                op=UnaryOpKind.SIZEOF,
                operand=b,
                location=a.location,
            )
        self.restore(z)

        if (
            (a := self.expect(TokenKind.ALIGNOF))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.type_name())
            and self.expect(TokenKind.R_PAREN)
        ):
            return UnaryOperator(
                op=UnaryOpKind.ALIGNOF,
                operand=b,
                location=a.location,
            )
        self.restore(z)

        if a := self.postfix_expression():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def cast_expression(self):
        """
        cast-expression:
            unary-expression
            ( type-name ) cast-expression
        """
        z = self.save()
        if a := self.unary_expression():
            return a
        self.restore(z)
        if (
            (a := self.expect(TokenKind.L_PAREN))
            and (b := self.type_name())
            and self.expect(TokenKind.R_PAREN)
            and (c := self.cast_expression())
        ):
            return ExplicitCast(type_name=b, expr=c, location=a.location)
        self.restore(z)
        return None

    @update_call_tree
    def multiplicative_expression(self):
        """
        multiplicative-expression:
            cast-expression
            multiplicative-expression * cast-expression
            multiplicative-expression / cast-expression
            multiplicative-expression % cast-expression
        """
        z = self.save()
        a = self.cast_expression()
        if a == None:
            self.restore(z)
            return None
        token_opkind = {
            TokenKind.STAR: BinOpKind.MUL,
            TokenKind.SLASH: BinOpKind.DIV,
            TokenKind.PERCENT: BinOpKind.MOD,
        }
        while self.curtoken().kind in token_opkind.keys():
            token = self.curtoken()
            if self.expect(token.kind) and (b := self.cast_expression()):
                a = BinaryOperator(
                    op=token_opkind[token.kind],
                    left=a,
                    right=b,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def additive_expression(self):
        """
        additive-expression:
            multiplicative-expression
            additive-expression + multiplicative-expression
            additive-expression - multiplicative-expression
        """
        z = self.save()
        a = self.multiplicative_expression()
        if a == None:
            self.restore(z)
            return None
        token_opkind = {
            TokenKind.PLUS: BinOpKind.ADD,
            TokenKind.MINUS: BinOpKind.SUB,
        }
        while self.curtoken().kind in token_opkind.keys():
            token = self.curtoken()
            if self.expect(token.kind) and (b := self.multiplicative_expression()):
                a = BinaryOperator(
                    op=token_opkind[token.kind],
                    left=a,
                    right=b,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def shift_expression(self):
        """
        shift-expression:
            additive-expression
            shift-expression << additive-expression
            shift-expression >> additive-expression
        """
        z = self.save()
        a = self.additive_expression()
        if a == None:
            self.restore(z)
            return None
        token_opkind = {
            TokenKind.LESSLESS: BinOpKind.LSHIFT,
            TokenKind.GREATERGREATER: BinOpKind.RSHIFT,
        }
        while self.curtoken().kind in token_opkind.keys():
            token = self.curtoken()
            if self.expect(token.kind) and (b := self.additive_expression()):
                a = BinaryOperator(
                    op=token_opkind[token.kind],
                    left=a,
                    right=b,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def relational_expression(self):
        """
        relational-expression:
            shift-expression
            relational-expression < shift-expression
            relational-expression > shift-expression
            relational-expression <= shift-expression
            relational-expression >= shift-expression
        """
        z = self.save()
        a = self.shift_expression()
        if a == None:
            self.restore(z)
            return None
        token_opkind = {
            TokenKind.LESS: BinOpKind.LT,
            TokenKind.GREATER: BinOpKind.GT,
            TokenKind.LESSEQUAL: BinOpKind.LTE,
            TokenKind.GREATEREQUAL: BinOpKind.GTE,
        }
        while self.curtoken().kind in token_opkind.keys():
            token = self.curtoken()
            if self.expect(token.kind) and (b := self.shift_expression()):
                a = BinaryOperator(
                    op=token_opkind[token.kind],
                    left=a,
                    right=b,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def equality_expression(self):
        """
        equality-expression:
            relational-expression
            equality-expression == relational-expression
            equality-expression != relational-expression
        """
        z = self.save()
        a = self.relational_expression()
        if a == None:
            self.restore(z)
            return None
        token_opkind = {
            TokenKind.EQUALEQUAL: BinOpKind.EQ,
            TokenKind.EXCLAIMEQUAL: BinOpKind.NEQ,
        }
        while self.curtoken().kind in token_opkind.keys():
            token = self.curtoken()
            if self.expect(token.kind) and (b := self.relational_expression()):
                a = BinaryOperator(
                    op=token_opkind[token.kind],
                    left=a,
                    right=b,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def AND_expression(self):
        """
        AND-expression:
            equality-expression
            AND-expression & equality-expression
        """
        z = self.save()
        a = self.equality_expression()
        if a == None:
            self.restore(z)
            return None
        token_opkind = {
            TokenKind.AMP: BinOpKind.BITAND,
        }
        while self.curtoken().kind in token_opkind.keys():
            token = self.curtoken()
            if self.expect(token.kind) and (b := self.equality_expression()):
                a = BinaryOperator(
                    op=token_opkind[token.kind],
                    left=a,
                    right=b,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def exclusive_OR_expression(self):
        """
        exclusive-OR-expression:
            AND-expression
            exclusive-OR-expression ^ AND-expression
        """
        z = self.save()
        a = self.AND_expression()
        if a == None:
            self.restore(z)
            return None
        token_opkind = {
            TokenKind.CARET: BinOpKind.BITXOR,
        }
        while self.curtoken().kind in token_opkind.keys():
            token = self.curtoken()
            if self.expect(token.kind) and (b := self.AND_expression()):
                a = BinaryOperator(
                    op=token_opkind[token.kind],
                    left=a,
                    right=b,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def inclusive_OR_expression(self):
        """
        inclusive-OR-expression:
            exclusive-OR-expression
            inclusive-OR-expression | exclusive-OR-expression
        """
        z = self.save()
        a = self.exclusive_OR_expression()
        if a == None:
            self.restore(z)
            return None
        token_opkind = {
            TokenKind.PIPE: BinOpKind.BITOR,
        }
        while self.curtoken().kind in token_opkind.keys():
            token = self.curtoken()
            if self.expect(token.kind) and (b := self.exclusive_OR_expression()):
                a = BinaryOperator(
                    op=token_opkind[token.kind],
                    left=a,
                    right=b,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def logical_AND_expression(self):
        """
        logical-AND-expression:
            inclusive-OR-expression
            logical-AND-expression && inclusive-OR-expression
        """
        z = self.save()
        a = self.inclusive_OR_expression()
        if a == None:
            self.restore(z)
            return None
        token_opkind = {
            TokenKind.AMPAMP: BinOpKind.AND,
        }
        while self.curtoken().kind in token_opkind.keys():
            token = self.curtoken()
            if self.expect(token.kind) and (b := self.inclusive_OR_expression()):
                a = BinaryOperator(
                    op=token_opkind[token.kind],
                    left=a,
                    right=b,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def logical_OR_expression(self):
        """
        logical-OR-expression:
            logical-AND-expression
            logical-OR-expression || logical-AND-expression
        """
        z = self.save()
        a = self.logical_AND_expression()
        if a == None:
            self.restore(z)
            return None
        token_opkind = {
            TokenKind.PIPEPIPE: BinOpKind.OR,
        }
        while self.curtoken().kind in token_opkind.keys():
            token = self.curtoken()
            if self.expect(token.kind) and (b := self.logical_AND_expression()):
                a = BinaryOperator(
                    op=token_opkind[token.kind],
                    left=a,
                    right=b,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def conditional_expression(self):
        """
        conditional-expression:
            logical-OR-expression
            logical-OR-expression ? expression : conditional-expression
        """
        z = self.save()
        a = self.logical_OR_expression()
        if a == None:
            self.restore(z)
            return None
        while self.curtoken().kind == TokenKind.QUESTION:
            token = self.curtoken()
            if (
                self.expect(TokenKind.QUESTION)
                and (b := self.expression())
                and self.expect(TokenKind.COLON)
                and (c := self.conditional_expression())
            ):
                a = ConditionalOperator(
                    condition_expr=a,
                    true_expr=b,
                    false_expr=c,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def assignment_expression(self):
        """
        assignment-expression:
            conditional-expression
            unary-expression assignment-operator assignment-expression
        assignment-operator: one of
            = *= /= %= += -= <<= >>= &= ^= |=
        """
        assignment_operator = {
            TokenKind.EQUAL: BinOpKind.ASSIGN,
            TokenKind.STAREQUAL: BinOpKind.AMUL,
            TokenKind.SLASHEQUAL: BinOpKind.ADIV,
            TokenKind.PERCENTEQUAL: BinOpKind.AMOD,
            TokenKind.PLUSEQUAL: BinOpKind.AADD,
            TokenKind.MINUSEQUAL: BinOpKind.ASUB,
            TokenKind.LESSLESSEQUAL: BinOpKind.ALSHIFT,
            TokenKind.GREATERGREATEREQUAL: BinOpKind.ARSHIFT,
            TokenKind.AMPEQUAL: BinOpKind.ABITAND,
            TokenKind.CARETEQUAL: BinOpKind.ABITXOR,
            TokenKind.PIPEEQUAL: BinOpKind.ABITOR,
        }
        z = self.save()
        if a := self.unary_expression():
            token = self.curtoken()
            if token.kind in assignment_operator.keys():
                if self.expect(token.kind) and (b := self.assignment_expression()):
                    return BinaryOperator(
                        op=assignment_operator[token.kind],
                        left=a,
                        right=b,
                        location=token.location,
                    )
        self.restore(z)
        if a := self.conditional_expression():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def expression(self):
        """
        expression:
            assignment-expression
            expression , assignment-expression
        """
        z = self.save()
        a = self.assignment_expression()
        if a == None:
            self.restore(z)
            return None
        token_opkind = {
            TokenKind.COMMA: BinOpKind.COMMA,
        }
        while self.curtoken().kind in token_opkind.keys():
            token = self.curtoken()
            if self.expect(token.kind) and (b := self.assignment_expression()):
                a = BinaryOperator(
                    op=token_opkind[token.kind],
                    left=a,
                    right=b,
                    location=token.location,
                )
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def constant_expression(self):
        """
        constant-expression:
            conditional-expression
        """
        return self.conditional_expression()

    @may_update_type_symbol
    @update_call_tree
    def declaration(self):
        """
        declaration:
            declaration-specifiers init-declarator-list[opt] ;
            attribute-specifier-sequence declaration-specifiers init-declarator-list ;
            static_assert-declaration
            attribute-declaration
        """
        z = self.save()
        token = self.curtoken()
        if (
            (a := self.declaration_specifiers()) != None
            and ((b := self.optional(self.init_declarator_list)),)
            and self.expect(TokenKind.SEMI)
        ):
            return DeclStmt(
                attribute_specifiers=[],
                specifiers=a[0],
                specifier_attributes=a[1],
                declarators=b,
                location=token.location,
            )
        self.restore(z)

        if (
            (a := self.attribute_specifier_sequence()) != None
            and (b := self.declaration_specifiers()) != None
            and ((c := self.optional(self.init_declarator_list)),)
            and self.expect(TokenKind.SEMI)
        ):
            return DeclStmt(
                attribute_specifiers=a,
                specifiers=b[0],
                specifier_attributes=b[1],
                declarators=c,
                location=token.location,
            )
        self.restore(z)

        if a := self.static_assert_declaration():
            return a
        self.restore(z)
        if a := self.attribute_declaration():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def declaration_specifiers(self) -> tuple[list[Node], list[Node]]:
        """
        declaration-specifiers:
            declaration-specifier attribute-specifier-sequence[opt]
            declaration-specifier declaration-specifiers
        """
        z = self.save()
        a = self.declaration_specifier()
        if a == None:
            self.restore(z)
            return None
        y = self.save()
        if (b := self.attribute_specifier_sequence()) != None:
            return ([a], b)
        self.restore(y)
        b = self.declaration_specifiers()
        if b == None:
            self.restore(y)
            b = ([], [])
        return ([a] + b[0], b[1])

    @update_call_tree
    def declaration_specifier(self):
        """
        declaration-specifier:
            storage-class-specifier
            type-specifier-qualifier
            function-specifier
        """
        z = self.save()
        if a := self.storage_class_specifier():
            return a
        self.restore(z)
        if a := self.type_specifier_qualifier():
            return a
        self.restore(z)
        if a := self.function_specifier():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def init_declarator_list(self):
        """
        init-declarator-list:
            init-declarator
            init-declarator-list , init-declarator
        """
        z = self.save()
        a = []
        b = self.init_declarator()
        if b == None:
            self.restore(z)
            return None
        a.append(b)
        while self.curtoken().kind == TokenKind.COMMA:
            if self.expect(TokenKind.COMMA) and (b := self.init_declarator()):
                a.append(b)
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def init_declarator(self):
        """
        init-declarator:
            declarator
            declarator = initializer
        """
        z = self.save()
        if (
            (a := self.declarator())
            and self.expect(TokenKind.EQUAL)
            and (b := self.initializer())
        ):
            return TypeOrVarDecl(
                declarator=a,
                initializer=b,
                location=a.location,
            )
        self.restore(z)
        if a := self.declarator():
            return TypeOrVarDecl(
                declarator=a,
                initializer=None,
                location=a.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def attribute_declaration(self):
        """
        attribute-declaration:
            attribute-specifier-sequence ;
        """
        z = self.save()
        token = self.curtoken()
        if (a := self.attribute_specifier_sequence()) != None and self.expect(
            TokenKind.SEMI
        ):
            return AttributeDeclStmt(
                attribute_specifiers=a,
                location=token.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def storage_class_specifier(self):
        """
        storage-class-specifier:
            auto
            constexpr
            extern
            register
            static
            thread_local
            typedef
        """
        token_specifier = {
            TokenKind.AUTO: StorageClassSpecifier.AUTO,
            TokenKind.CONSTEXPR: StorageClassSpecifier.CONSTEXPR,
            TokenKind.EXTERN: StorageClassSpecifier.EXTERN,
            TokenKind.REGISTER: StorageClassSpecifier.REGISTER,
            TokenKind.STATIC: StorageClassSpecifier.STATIC,
            TokenKind.THREAD_LOCAL: StorageClassSpecifier.THREAD_LOCAL,
            TokenKind.TYPEDEF: StorageClassSpecifier.TYPEDEF,
        }
        z = self.save()
        token = self.curtoken()
        if token.kind in token_specifier.keys() and self.expect(token.kind):
            return StorageClass(
                specifier=token_specifier[token.kind],
                location=token.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def type_specifier(self):
        """
        type-specifier:
            void
            char
            short
            int
            long
            float
            double
            signed
            unsigned
            _BitInt ( constant-expression )
            bool
            _Complex
            _Decimal32
            _Decimal64
            _Decimal128
            atomic-type-specifier
            struct-or-union-specifier
            enum-specifier
            typedef-name
            typeof-specifier
        """
        z = self.save()
        token = self.curtoken()
        if (
            self.expect(TokenKind.VOID)
            or self.expect(TokenKind.CHAR)
            or self.expect(TokenKind.SHORT)
            or self.expect(TokenKind.INT)
            or self.expect(TokenKind.LONG)
            or self.expect(TokenKind.FLOAT)
            or self.expect(TokenKind.DOUBLE)
            or self.expect(TokenKind.SIGNED)
            or self.expect(TokenKind.UNSIGNED)
            or self.expect(TokenKind.BOOL)
            or self.expect(TokenKind._COMPLEX)
            or self.expect(TokenKind._DECIMAL32)
            or self.expect(TokenKind._DECIMAL64)
            or self.expect(TokenKind._DECIMAL128)
        ):
            return BasicTypeSpecifier(
                specifier_name=token.text,
                location=token.location,
            )
        self.restore(z)

        if (
            (a := self.expect(TokenKind._BITINT))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.constant_expression())
            and self.expect(TokenKind.R_PAREN)
        ):
            return BitIntSpecifier(
                size=b,
                location=a.location,
            )
        self.restore(z)

        if a := self.atomic_type_specifier():
            return a
        self.restore(z)
        if a := self.struct_or_union_specifier():
            return a
        self.restore(z)
        if a := self.enum_specifier():
            return a
        self.restore(z)
        if a := self.typedef_name():
            return a
        self.restore(z)
        if a := self.typeof_specifier():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def struct_or_union_specifier(self):
        """
        struct-or-union-specifier:
            struct-or-union attribute-specifier-sequence[opt] identifier[opt] { member-declaration-list }
            struct-or-union attribute-specifier-sequence[opt] identifier
        struct-or-union:
            struct
            union
        """
        z = self.save()
        if (
            (a := (self.expect(TokenKind.STRUCT) or self.expect(TokenKind.UNION)))
            and ((b := self.optional(self.attribute_specifier_sequence)),)
            and ((c := self.optional(lambda: self.expect(TokenKind.IDENTIFIER)),))
            and self.expect(TokenKind.L_BRACE)
            and (d := self.member_declaration_list()) != None
            and self.expect(TokenKind.R_BRACE)
        ):
            return RecordDecl(
                struct_or_union=a.text,
                attribute_specifiers=b,
                name=c.text if c != None else "",
                members_declaration=d,
                location=a.location,
            )
        self.restore(z)
        if (
            (a := (self.expect(TokenKind.STRUCT) or self.expect(TokenKind.UNION)))
            and ((b := self.optional(self.attribute_specifier_sequence)),)
            and (c := self.expect(TokenKind.IDENTIFIER))
        ):
            return RecordDecl(
                struct_or_union=a.text,
                attribute_specifiers=b,
                name=c.text if c != None else "",
                members_declaration=None,
                location=a.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def member_declaration_list(self):
        """
        member-declaration-list:
            member-declaration
            member-declaration-list member-declaration
        """
        z = self.save()
        a = []
        b = self.member_declaration()
        if b == None:
            self.restore(b)
            return None
        a.append(b)
        while self.curtoken().kind == TokenKind.R_BRACE:
            if b := self.member_declaration():
                a.append(b)
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def member_declaration(self):
        """
        member-declaration:
            attribute-specifier-sequence[opt] specifier-qualifier-list member-declarator-list[opt] ;
            static_assert-declaration
        """
        z = self.save()
        if a := self.static_assert_declaration():
            return a
        self.restore(z)
        token = self.curtoken()
        if (
            ((a := self.optional(self.attribute_specifier_sequence)),)
            and (b := self.specifier_qualifier_list()) != None
            and ((c := self.optional(self.member_declarator_list)),)
            and self.expect(TokenKind.SEMI)
        ):
            return FieldDecl(
                attribute_specifiers=a,
                specifiers=b[0],
                specifier_attributes=b[1],
                declarators=c,
                location=token.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def specifier_qualifier_list(self) -> tuple[list[Node], list[Node]]:
        """
        specifier-qualifier-list:
            type-specifier-qualifier attribute-specifier-sequence[opt]
            type-specifier-qualifier specifier-qualifier-list
        """
        z = self.save()
        a = self.type_specifier_qualifier()
        if a == None:
            self.restore(z)
            return None
        y = self.save()
        if (b := self.attribute_specifier_sequence()) != None:
            return ([a], b)
        self.restore(y)
        b = self.specifier_qualifier_list()
        if b == None:
            self.restore(y)
            b = ([], [])
        return ([a] + b[0], b[1])

    @update_call_tree
    def type_specifier_qualifier(self):
        """
        type-specifier-qualifier:
            type-specifier
            type-qualifier
            alignment-specifier
        """
        z = self.save()
        if a := self.type_specifier():
            return a
        self.restore(z)
        if a := self.type_qualifier():
            return a
        self.restore(z)
        if a := self.alignment_specifier():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def member_declarator_list(self):
        """
        member-declarator-list:
            member-declarator
            member-declarator-list , member-declarator
        """
        z = self.save()
        a = []
        b = self.member_declarator()
        if b == None:
            self.restore(z)
            return None
        a.append(b)
        while self.curtoken().kind == TokenKind.COMMA:
            if self.expect(TokenKind.COMMA) and (b := self.member_declarator()):
                a.append(b)
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def member_declarator(self):
        """
        member-declarator:
            declarator
            declarator[opt] : constant-expression
        """
        z = self.save()
        token = self.curtoken()
        if (
            ((a := self.optional(self.declarator)),)
            and self.expect(TokenKind.COLON)
            and (b := self.constant_expression())
        ):
            return MemberDecl(declarator=a, bit_field=b, location=token.location)
        self.restore(z)
        if a := self.declarator():
            return MemberDecl(declarator=a, bit_field=None, location=token.location)
        self.restore(z)
        return None

    @update_call_tree
    def enum_specifier(self):
        """
        enum-specifier:
            enum attribute-specifier-sequence[opt] identifier[opt] enum-type-specifier[opt]
                { enumerator-list }
            enum attribute-specifier-sequence[opt] identifier[opt] enum-type-specifier[opt]
                { enumerator-list , }
            enum identifier enum-type-specifier[opt]
        """
        z = self.save()
        if (
            (a := self.expect(TokenKind.ENUM))
            and ((b := self.optional(self.attribute_specifier_sequence)),)
            and ((c := self.optional(lambda: self.expect(TokenKind.IDENTIFIER))),)
            and ((d := self.optional(self.enum_type_specifier)),)
            and self.expect(TokenKind.L_BRACE)
            and ((e := self.optional(self.enumerator_list)),)
            and (self.optional(lambda: self.expect(TokenKind.SEMI)),)
            and self.expect(TokenKind.R_BRACE)
        ):
            c: Token
            return EnumDecl(
                attribute_specifiers=b,
                name=c.text if c != None else "",
                specifiers=d,
                enumerators=e,
                location=a.location,
            )
        self.restore(z)
        if (
            (a := self.expect(TokenKind.ENUM))
            and (b := self.expect(TokenKind.IDENTIFIER))
            and ((c := self.optional(self.enum_type_specifier)),)
        ):
            return EnumDecl(
                attribute_specifiers=None,
                name=b.text,
                specifiers=c,
                enumerators=None,
                location=a.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def enumerator_list(self):
        """
        enumerator-list:
            enumerator
            enumerator-list , enumerator
        """
        z = self.save()
        a = []
        b = self.enumerator()
        if b == None:
            self.restore(z)
            return None
        a.append(b)
        while self.curtoken().kind == TokenKind.COMMA:
            if self.expect(TokenKind.COMMA) and (b := self.enumerator()):
                a.append(b)
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def enumerator(self):
        """
        enumerator:
            enumeration-constant attribute-specifier-sequence[opt]
            enumeration-constant attribute-specifier-sequence[opt] = constant-expression
        """
        z = self.save()
        if (
            (a := self.expect(TokenKind.IDENTIFIER))
            and ((b := self.optional(self.attribute_specifier_sequence)),)
            and self.expect(TokenKind.EQUAL)
            and (c := self.constant_expression())
        ):
            return Enumerator(
                name=a.text,
                attribute_specifiers=b,
                value=c,
                location=a.location,
            )
        self.restore(z)
        if (a := self.expect(TokenKind.IDENTIFIER)) and (
            (b := self.optional(self.attribute_specifier_sequence),),
        ):
            return Enumerator(
                name=a.text,
                attribute_specifiers=b,
                value=None,
                location=a.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def enum_type_specifier(self):
        """
        enum-type-specifier:
            : specifier-qualifier-list
        """
        z = self.save()
        if (
            self.expect(TokenKind.COLON)
            and (a := self.specifier_qualifier_list()) != None
        ):
            return a
        self.restore(z)
        return None

    @update_call_tree
    def atomic_type_specifier(self):
        """
        atomic-type-specifier:
            _Atomic ( type-name )
        """
        z = self.save()
        if (
            (a := self.expect(TokenKind._ATOMIC))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.type_name())
            and self.expect(TokenKind.R_PAREN)
        ):
            return AtomicSpecifier(type_name=b, location=a.location)
        self.restore(z)
        return None

    @update_call_tree
    def typeof_specifier(self):
        """
        typeof-specifier:
            typeof ( typeof-specifier-argument )
            typeof_unqual ( typeof-specifier-argument )
        """
        z = self.save()
        if (
            (a := self.expect(TokenKind.TYPEOF))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.typeof_specifier_argument())
            and self.expect(TokenKind.R_PAREN)
        ):
            return TypeOfSpecifier(arg=b, location=a.location)
        self.restore(z)
        if (
            (a := self.expect(TokenKind.TYPEOF_UNQUAL))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.typeof_specifier_argument())
            and self.expect(TokenKind.R_PAREN)
        ):
            return TypeOfSpecifier(arg=b, location=a.location)
        self.restore(z)
        return None

    @update_call_tree
    def typeof_specifier_argument(self):
        """
        typeof-specifier-argument:
            expression
            type-name
        """
        z = self.save()
        if a := self.expression():
            return a
        self.restore(z)
        if a := self.type_name():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def type_qualifier(self):
        """
        type-qualifier:
            const
            restrict
            volatile
            _Atomic
        """
        z = self.save()
        if a := (
            self.expect(TokenKind.CONST)
            or self.expect(TokenKind.RESTRICT)
            or self.expect(TokenKind.VOLATILE)
            or self.expect(TokenKind._ATOMIC)
        ):
            return TypeQualifier(qualifier_name=a.text, location=a.location)
        self.restore(z)
        return None

    @update_call_tree
    def function_specifier(self):
        """
        function-specifier:
            inline
            _Noreturn
        """
        z = self.save()
        if a := (self.expect(TokenKind.INLINE) or self.expect(TokenKind._NORETURN)):
            return FunctionSpecifier(specifier_name=a.text, location=a.location)
        self.restore(z)
        return None

    @update_call_tree
    def typedef_name(self):
        """
        typedef-name:
            identifier
        """
        z = self.save()
        if (a := self.expect(TokenKind.IDENTIFIER)) and a.text in self.type_symbol:
            return TypedefSpecifier(
                specifier_name=a.text,
                location=a.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def alignment_specifier(self):
        """
        alignment-specifier:
            alignas ( type-name )
            alignas ( constant-expression )
        """
        z = self.save()
        if (
            (a := self.expect(TokenKind.ALIGNAS))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.type_name())
            and self.expect(TokenKind.R_PAREN)
        ):
            return AlignSepcifier(type_or_expr=b, location=a.location)
        self.restore(z)
        if (
            (a := self.expect(TokenKind.ALIGNAS))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.constant_expression())
            and self.expect(TokenKind.R_PAREN)
        ):
            return AlignSepcifier(type_or_expr=b, location=a.location)
        self.restore(z)
        return None

    @update_call_tree
    def declarator(self):
        """
        declarator:
            pointer[opt] direct-declarator
        """
        z = self.save()
        if (a := self.optional(self.pointer),) and (b := self.direct_declarator()):
            if a == None:
                return b
            # 将direct_declarator接到pointer后面
            c = a
            while c.declarator != None:
                c = c.declarator
            c.declarator = b
            return a
        self.restore(z)
        return None

    @update_call_tree
    def direct_declarator(self) -> Declarator:
        """
        direct-declarator:
            identifier attribute-specifier-sequence[opt]
            ( declarator )
            array-declarator attribute-specifier-sequence[opt]
            function-declarator attribute-specifier-sequence[opt]

        array-declarator:
            direct-declarator [ type-qualifier-list[opt] assignment-expression[opt] ]
            direct-declarator [ static type-qualifier-list[opt] assignment-expression ]
            direct-declarator [ type-qualifier-list static assignment-expression ]
            direct-declarator [ type-qualifier-list[opt] * ]

        function-declarator:
            direct-declarator ( parameter-type-list[opt] )
        """
        z = self.save()
        if (a := self.expect(TokenKind.IDENTIFIER)) and (
            (b := self.optional(self.attribute_specifier_sequence)),
        ):
            a = NameDeclarator(
                name=a.text,
                declarator=None,
                attribute_specifiers=b,
                location=a.location,
            )
        else:
            self.restore(z)

            if not (
                self.expect(TokenKind.L_PAREN)
                and (a := self.declarator())
                and self.expect(TokenKind.R_PAREN)
            ):
                self.restore(z)
                return None

        while self.curtoken().kind in (TokenKind.L_PAREN, TokenKind.L_SQUARE):
            token = self.curtoken()
            if token.kind == TokenKind.L_SQUARE:
                if (
                    self.expect(TokenKind.L_SQUARE)
                    and ((b := self.optional(self.type_qualifier_list)),)
                    and ((c := self.optional(self.assignment_expression)),)
                    and self.expect(TokenKind.R_SQUARE)
                    and ((d := self.optional(self.attribute_specifier_sequence)),)
                ):
                    a = ArrayDeclarator(
                        declarator=a,
                        qualifiers=b if b != None else [],
                        size=c,
                        is_star_modified=False,
                        is_static=False,
                        attribute_specifiers=d,
                        location=token.location,
                    )
                    continue
                self.restore(z)
                if (
                    self.expect(TokenKind.L_SQUARE)
                    and self.expect(TokenKind.STATIC)
                    and ((b := self.optional(self.type_qualifier_list)),)
                    and (c := self.assignment_expression())
                    and self.expect(TokenKind.R_SQUARE)
                    and ((d := self.optional(self.attribute_specifier_sequence)),)
                ):
                    a = ArrayDeclarator(
                        declarator=a,
                        qualifiers=b if b != None else [],
                        size=c,
                        is_star_modified=False,
                        is_static=True,
                        attribute_specifiers=d,
                        location=token.location,
                    )
                    continue
                self.restore(z)
                if (
                    self.expect(TokenKind.L_SQUARE)
                    and (b := self.type_qualifier_list()) != None
                    and self.expect(TokenKind.STATIC)
                    and (c := self.assignment_expression())
                    and self.expect(TokenKind.R_SQUARE)
                    and ((d := self.optional(self.attribute_specifier_sequence)),)
                ):
                    a = ArrayDeclarator(
                        declarator=a,
                        qualifiers=b if b != None else [],
                        size=c,
                        is_star_modified=False,
                        is_static=True,
                        attribute_specifiers=d,
                        location=token.location,
                    )
                    continue
                self.restore(z)
                if (
                    self.expect(TokenKind.L_SQUARE)
                    and (b := self.optional(self.type_qualifier_list),)
                    and self.expect(TokenKind.STAR)
                    and self.expect(TokenKind.R_SQUARE)
                    and ((d := self.optional(self.attribute_specifier_sequence)),)
                ):
                    a = ArrayDeclarator(
                        declarator=a,
                        qualifiers=b if b != None else [],
                        size=None,
                        is_star_modified=True,
                        is_static=False,
                        attribute_specifiers=d,
                        location=token.location,
                    )
                    continue
                break
            elif token.kind == TokenKind.L_PAREN:
                if (
                    self.expect(TokenKind.L_PAREN)
                    and ((b := self.optional(self.parameter_type_list)),)
                    and self.expect(TokenKind.R_PAREN)
                    and ((d := self.optional(self.attribute_specifier_sequence)),)
                ):
                    if b == None:
                        b = [[], False]
                    a = FunctionDeclarator(
                        declarator=a,
                        parameters=b[0],
                        has_varparam=b[1],
                        attribute_specifiers=d,
                        location=token.location,
                    )
                    continue
                break
        else:
            return a
        self.restore(z)
        return None

    @update_call_tree
    def pointer(self):
        """
        pointer:
            * attribute-specifier-sequence[opt] type-qualifier-list[opt]
            * attribute-specifier-sequence[opt] type-qualifier-list[opt] pointer
        """
        z = self.save()
        if (
            (b := self.expect(TokenKind.STAR))
            and ((c := self.optional(self.attribute_specifier_sequence)),)
            and ((d := self.optional(self.type_qualifier_list)),)
            and ((e := self.optional(self.pointer)),)
        ):
            return PointerDeclarator(
                declarator=e,
                attribute_specifiers=c,
                qualifiers=d,
                location=b.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def type_qualifier_list(self):
        """
        type-qualifier-list:
            type-qualifier
            type-qualifier-list type-qualifier
        """
        z = self.save()
        a = []
        b = self.type_qualifier()
        if b == None:
            self.restore(z)
            return None
        a.append(b)
        while self.lookahead(
            TokenKind.CONST, TokenKind.RESTRICT, TokenKind.VOLATILE, TokenKind._ATOMIC
        ):
            if b := self.type_qualifier():
                a.append(b)
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def parameter_type_list(self) -> tuple[list[Node], bool]:
        """
        parameter-type-list:
            parameter-list
            parameter-list , ...
            ...
        """
        z = self.save()
        if self.expect(TokenKind.ELLIPSIS):
            return ([], True)
        self.restore(z)

        if (
            (a := self.parameter_list()) != None
            and self.expect(TokenKind.COMMA)
            and self.expect(TokenKind.ELLIPSIS)
        ):
            return (a, True)
        self.restore(z)

        if (a := self.parameter_list()) != None:
            return (a, False)
        self.restore(z)
        return None

    @update_call_tree
    def parameter_list(self):
        """
        parameter-list:
            parameter-declaration
            parameter-list , parameter-declaration
        """
        z = self.save()
        a = []
        b = self.parameter_declaration()
        if b == None:
            self.restore(z)
            return None
        a.append(b)
        while self.curtoken().kind == TokenKind.COMMA:
            if self.expect(TokenKind.COMMA) and (b := self.parameter_declaration()):
                a.append(b)
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def parameter_declaration(self):
        """
        parameter-declaration:
            attribute-specifier-sequence[opt] declaration-specifiers declarator
            attribute-specifier-sequence[opt] declaration-specifiers abstract-declarator[opt]
        """
        z = self.save()
        token = self.curtoken()
        if (
            ((a := self.optional(self.attribute_specifier_sequence)),)
            and (b := self.declaration_specifiers())
            and (c := self.declarator())
        ):
            return ParamDecl(
                attribute_specifiers=a,
                specifiers=b[0],
                declarator=c,
                location=token.location,
            )
        self.restore(z)
        if (
            ((a := self.optional(self.attribute_specifier_sequence)),)
            and (b := self.declaration_specifiers())
            and ((c := self.optional(self.abstract_declarator)),)
        ):
            return ParamDecl(
                attribute_specifiers=a,
                specifiers=b,
                declarator=c,
                location=token.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def type_name(self) -> TypeName:
        """
        type-name:
            specifier-qualifier-list abstract-declarator[opt]
        """
        z = self.save()
        token = self.curtoken()
        if (a := self.specifier_qualifier_list()) != None and (
            (b := self.optional(self.abstract_declarator)),
        ):
            return TypeName(
                specifiers=a[0],
                specifiers_attributes=a[1],
                declarator=b,
                location=token.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def abstract_declarator(self):
        """
        abstract-declarator:
            pointer
            pointer[opt] direct-abstract-declarator
        """
        z = self.save()
        if ((a := self.optional(self.pointer)),) and (
            b := self.direct_abstract_declarator()
        ):
            c = b
            while c.declarator != None:
                c = c.declarator
            c.declarator = a
            return b
        self.restore(z)
        if a := self.pointer():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def direct_abstract_declarator(self) -> Declarator:
        """
        direct-abstract-declarator:
            ( abstract-declarator )
            array-abstract-declarator attribute-specifier-sequence[opt]
            function-abstract-declarator attribute-specifier-sequence[opt]

        array-abstract-declarator:
            direct-abstract-declarator[opt] [ type-qualifier-list[opt] assignment-expression[opt] ]
            direct-abstract-declarator[opt] [ static type-qualifier-list[opt] assignment-expression ]
            direct-abstract-declarator[opt] [ type-qualifier-list static assignment-expression ]
            direct-abstract-declarator[opt] [ * ]

        function-abstract-declarator:
            direct-abstract-declarator[opt] ( parameter-type-list[opt] )
        """
        z = self.save()
        a = None
        if not (
            self.expect(TokenKind.L_PAREN)
            and (a := self.abstract_declarator())
            and self.expect(TokenKind.R_PAREN)
        ):
            self.restore(z)
        while self.curtoken().kind in (TokenKind.L_SQUARE, TokenKind.L_PAREN):
            token = self.curtoken()
            if token.kind == TokenKind.L_SQUARE:
                if (
                    self.expect(TokenKind.L_SQUARE)
                    and ((b := self.optional(self.type_qualifier_list)),)
                    and ((c := self.optional(self.assignment_expression)),)
                    and self.expect(TokenKind.R_SQUARE)
                    and ((d := self.optional(self.attribute_specifier_sequence)),)
                ):
                    a = ArrayDeclarator(
                        declarator=a,
                        qualifiers=b if b != None else [],
                        size=c,
                        is_star_modified=False,
                        is_static=False,
                        attribute_specifiers=d,
                        location=token.location,
                    )
                    continue
                self.restore(z)
                if (
                    self.expect(TokenKind.L_SQUARE)
                    and self.expect(TokenKind.STATIC)
                    and ((b := self.optional(self.type_qualifier_list)),)
                    and (c := self.assignment_expression())
                    and self.expect(TokenKind.R_SQUARE)
                    and ((d := self.optional(self.attribute_specifier_sequence)),)
                ):
                    a = ArrayDeclarator(
                        declarator=a,
                        qualifiers=b if b != None else [],
                        size=c,
                        is_star_modified=False,
                        is_static=True,
                        attribute_specifiers=d,
                        location=token.location,
                    )
                    continue
                self.restore(z)
                if (
                    self.expect(TokenKind.L_SQUARE)
                    and (b := self.type_qualifier_list()) != None
                    and self.expect(TokenKind.STATIC)
                    and (c := self.assignment_expression())
                    and self.expect(TokenKind.R_SQUARE)
                    and ((d := self.optional(self.attribute_specifier_sequence)),)
                ):
                    a = ArrayDeclarator(
                        declarator=a,
                        qualifiers=b if b != None else [],
                        size=c,
                        is_star_modified=False,
                        is_static=True,
                        attribute_specifiers=d,
                        location=token.location,
                    )
                    continue
                self.restore(z)
                if (
                    self.expect(TokenKind.L_SQUARE)
                    and self.expect(TokenKind.STAR)
                    and self.expect(TokenKind.R_SQUARE)
                    and ((d := self.optional(self.attribute_specifier_sequence)),)
                ):
                    a = ArrayDeclarator(
                        declarator=a,
                        qualifiers=[],
                        size=None,
                        is_star_modified=True,
                        is_static=False,
                        attribute_specifiers=d,
                        location=token.location,
                    )
                    continue
                break
            elif token.kind == TokenKind.L_PAREN:
                if (
                    self.expect(TokenKind.L_PAREN)
                    and ((b := self.optional(self.parameter_type_list)),)
                    and self.expect(TokenKind.R_PAREN)
                    and ((d := self.optional(self.attribute_specifier_sequence)),)
                ):
                    if b == None:
                        b = [[], False]
                    a = FunctionDeclarator(
                        declarator=a,
                        parameters=b[0],
                        has_varparam=b[1],
                        attribute_specifiers=d,
                        location=token.location,
                    )
                    continue
                break
        else:
            return a
        self.restore(z)
        return None

    @update_call_tree
    def braced_initializer(self):
        """
        braced-initializer:
            { }
            { initializer-list }
            { initializer-list , }
        """
        z = self.save()
        if (
            self.expect(TokenKind.L_BRACE)
            and (a := self.initializer_list()) != None
            and self.expect(TokenKind.COMMA)
            and self.expect(TokenKind.R_BRACE)
        ):
            return a
        self.restore(z)
        if (
            self.expect(TokenKind.L_BRACE)
            and (a := self.initializer_list()) != None
            and self.expect(TokenKind.R_BRACE)
        ):
            return a
        self.restore(z)
        if (a := self.expect(TokenKind.L_BRACE)) and self.expect(TokenKind.R_BRACE):
            return InitList(initializers=[], location=a.location)
        self.restore(z)
        return None

    @update_call_tree
    def initializer(self):
        """
        initializer:
            assignment-expression
            braced-initializer
        """
        z = self.save()
        if a := self.assignment_expression():
            return a
        self.restore(z)
        if a := self.braced_initializer():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def initializer_list(self):
        """
        initializer-list:
            designation[opt] initializer
            initializer-list , designation[opt] initializer
        """
        z = self.save()
        a = []
        b = self.designation()
        if b != None:
            b.initializer = self.initializer()
            if b.initializer == None:
                self.restore(z)
                return None
            a.append(b)
        else:
            b = self.initializer()
            if b == None:
                self.restore(z)
                return None
            a.append(b)
        while self.curtoken().kind == TokenKind.COMMA:
            b = self.designation()
            if b != None:
                b.initializer = self.initializer()
                if b.initializer == None:
                    self.restore(z)
                    return None
                a.append(b)
            else:
                b = self.initializer()
                if b == None:
                    self.restore(z)
                    return None
                a.append(b)
        return a

    @update_call_tree
    def designation(self) -> Designation:
        """
        designation:
            designator-list =
        """
        z = self.save()
        token = self.curtoken()
        if (a := self.designator_list()) != None and self.expect(TokenKind.EQUAL):
            return Designation(designators=a, location=token.location)
        self.restore(z)
        return None

    @update_call_tree
    def designator_list(self):
        """
        designator-list:
            designator
            designator-list designator
        """
        z = self.save()
        a = []
        b = self.designator()
        if b == None:
            self.restore(z)
            return None
        a.append(b)
        while self.curtoken().kind != TokenKind.EQUAL:
            if b := self.designator():
                a.append(b)
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def designator(self):
        """
        designator:
            [ constant-expression ]
            . identifier
        """
        z = self.save()
        if (
            (a := self.expect(TokenKind.L_SQUARE))
            and (b := self.constant_expression())
            and self.expect(TokenKind.R_SQUARE)
        ):
            return Designator(index=b, location=a.location)
        self.restore(z)
        if (a := self.expect(TokenKind.PERIOD)) and (
            b := self.expect(TokenKind.IDENTIFIER)
        ):
            return Designator(member=b.text, location=a.location)
        self.restore(z)
        return None

    @update_call_tree
    def static_assert_declaration(self):
        """
        static_assert-declaration:
            static_assert ( constant-expression , string-literal ) ;
            static_assert ( constant-expression ) ;
        """
        z = self.save()
        if (
            (a := self.expect(TokenKind.STATIC_ASSERT))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.constant_expression())
            and self.expect(TokenKind.COMMA)
            and (c := self.expect(TokenKind.STRINGLITERAL))
            and self.expect(TokenKind.R_PAREN)
            and self.expect(TokenKind.SEMI)
        ):
            return StaticAssert(
                condition_expr=b,
                message=c.text,
                location=a.location,
            )
        self.restore(z)
        if (
            (a := self.expect(TokenKind.STATIC_ASSERT))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.constant_expression())
            and self.expect(TokenKind.R_PAREN)
            and self.expect(TokenKind.SEMI)
        ):
            return StaticAssert(
                condition_expr=b,
                message="",
                location=a.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def attribute_specifier_sequence(self):
        """
        attribute-specifier-sequence:
            attribute-specifier-sequence[opt] attribute-specifier
        """
        z = self.save()
        a = []
        b = self.attribute_specifier()
        if b == None:
            self.restore(z)
            return None
        a.append(b)
        while self.lookahead(TokenKind.L_SQUARE, TokenKind.L_SQUARE):
            if b := self.attribute_specifier():
                a.append(b)
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def attribute_specifier(self):
        """
        attribute-specifier:
            [ [ attribute-list ] ]
        """
        z = self.save()
        token = self.curtoken()
        if (
            self.expect(TokenKind.L_SQUARE)
            and self.expect(TokenKind.L_SQUARE)
            and (a := self.attribute_list())
            and self.expect(TokenKind.R_SQUARE)
            and self.expect(TokenKind.R_SQUARE)
        ):
            return AttributeSpecifier(attributes=a, location=token.location)
        self.restore(z)
        return None

    @update_call_tree
    def attribute_list(self):
        """
        attribute-list:
            attribute[opt]
            attribute-list , attribute[opt]
        """
        z = self.save()
        a = []
        b = self.attribute()
        if b != None:
            a.append(b)
        else:
            self.restore(z)
        while self.curtoken().kind == TokenKind.COMMA:
            self.expect(TokenKind.COMMA)
            if self.curtoken().kind in (TokenKind.COMMA, TokenKind.R_SQUARE):
                continue
            b = self.attribute()
            if b != None:
                a.append(b)
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def attribute(self):
        """
        attribute:
            attribute-token attribute-argument-clause[opt]
        """
        z = self.save()
        a = self.attribute_token()
        if a == None:
            self.restore(z)
            return None
        z = self.save()
        b = self.attribute_argument_clause()
        if b != None:
            a.args = b
        else:
            self.restore(z)
        return a

    @update_call_tree
    def attribute_token(self) -> Attribute:
        """
        attribute-token:
            standard-attribute
            attribute-prefixed-token

        attribute-prefixed-token:
            attribute-prefix :: identifier
        attribute-prefix:
            identifier
        """
        z = self.save()
        token = self.curtoken()
        if token.kind == TokenKind.IDENTIFIER:
            standard_attribute = {
                "deprecated": DeprecatedAttr,
                "fallthrough": FallthroughAttr,
                "maybe_unused": MaybeUnusedAttr,
                "nodiscard": NodiscardAttr,
                "noreturn": NoReturnAttr,
                "_Noreturn": NoReturnAttr,
                "unsequenced": UnsequencedAttr,
                "reproducible": ReproducibleAttr,
            }
            if token.text in standard_attribute:
                self.expect(TokenKind.IDENTIFIER)
                return standard_attribute[token.text](location=token.location)
            if (
                self.expect(TokenKind.IDENTIFIER)
                and self.expect(TokenKind.COLONCOLON)
                and (b := self.expect(TokenKind.IDENTIFIER))
            ):
                return Attribute(
                    prefix_name=token.text,
                    name=b.text,
                    location=token.location,
                )
        self.restore(z)
        return None

    @update_call_tree
    def attribute_argument_clause(self):
        """
        attribute-argument-clause:
            ( balanced-token-sequence[opt] )
        """
        z = self.save()
        if (
            self.expect(TokenKind.L_PAREN)
            and ((a := self.optional(self.balanced_token_sequence)) != None,)
            and self.expect(TokenKind.R_PAREN)
        ):
            return a if a != None else []
        self.restore(z)
        return None

    @update_call_tree
    def balanced_token_sequence(self):
        """
        balanced-token-sequence:
            balanced-token
            balanced-token-sequence balanced-token
        """
        z = self.save()
        a = []
        b = self.balanced_token()
        if b == None:
            self.restore(z)
            return None
        a.append(b)
        while self.curtoken().kind not in (
            TokenKind.R_PAREN,
            TokenKind.R_SQUARE,
            TokenKind.R_BRACE,
        ):
            if b := self.balanced_token():
                a.append(b)
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def balanced_token(self):
        """
        balanced-token:
            ( balanced-token-sequence[opt] )
            [ balanced-token-sequence[opt] ]
            { balanced-token-sequence[opt] }
            any token other than a parenthesis, a bracket, or a brace
        """
        z = self.save()
        if (
            self.expect(TokenKind.L_PAREN)
            and ((a := self.optional(self.balanced_token_sequence)),)
            and self.expect(TokenKind.R_PAREN)
        ):
            return a
        self.restore(z)
        if (
            self.expect(TokenKind.L_SQUARE)
            and ((a := self.optional(self.balanced_token_sequence)),)
            and self.expect(TokenKind.L_SQUARE)
        ):
            return a
        self.restore(z)
        if (
            self.expect(TokenKind.L_BRACE)
            and ((a := self.optional(self.balanced_token_sequence)),)
            and self.expect(TokenKind.R_BRACE)
        ):
            return a
        a = self.expect(self.curtoken().kind)
        return a

    @update_call_tree
    def statement(self):
        """
        statement:
            labeled-statement
            unlabeled-statement
        """
        z = self.save()
        if a := self.labeled_statement():
            return a
        self.restore(z)
        if a := self.unlabeled_statement():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def unlabeled_statement(self):
        """
        unlabeled-statement:
            expression-statement
            attribute-specifier-sequence[opt] primary-block
            attribute-specifier-sequence[opt] jump-statement
        """
        z = self.save()
        if a := self.expression_statement():
            return a
        self.restore(z)
        b = self.optional(self.attribute_specifier_sequence)
        z = self.save()
        if a := self.primary_block():
            a.attribute_specifiers = b
            return a
        self.restore(z)
        if a := self.jump_statement():
            a.attribute_specifiers = b
            return a
        self.restore(z)
        return None

    @update_call_tree
    def primary_block(self) -> Stmt:
        """
        primary-block:
            compound-statement
            selection-statement
            iteration-statement
        """
        z = self.save()
        if a := self.compound_statement():
            return a
        self.restore(z)
        if a := self.selection_statement():
            return a
        self.restore(z)
        if a := self.iteration_statement():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def secondary_block(self):
        """
        secondary-block:
            statement
        """
        z = self.save()
        if a := self.statement():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def label(self) -> Union[LabelStmt, CaseStmt, DefaultStmt]:
        """
        label:
            attribute-specifier-sequence[opt] identifier :
            attribute-specifier-sequence[opt] case constant-expression :
            attribute-specifier-sequence[opt] default :
        """
        b = self.optional(self.attribute_specifier_sequence)
        z = self.save()
        if (a := self.expect(TokenKind.IDENTIFIER)) and self.expect(TokenKind.COLON):
            return LabelStmt(
                name=a.text,
                attribute_specifiers=b,
                location=a.location,
            )
        self.restore(z)
        if (
            (a := self.expect(TokenKind.CASE))
            and (c := self.constant_expression())
            and self.expect(TokenKind.COLON)
        ):
            return CaseStmt(
                expr=c,
                attribute_specifiers=b,
                location=a.location,
            )
        self.restore(z)
        if (a := self.expect(TokenKind.DEFAULT)) and self.expect(TokenKind.COLON):
            return DefaultStmt(
                attribute_specifiers=b,
                location=a.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def labeled_statement(self):
        """
        labeled-statement:
            label statement
        """
        z = self.save()
        if (a := self.label()) and (b := self.statement()):
            a.stmt = b
            return a
        self.restore(z)
        return None

    @may_enter_scope
    @update_call_tree
    def compound_statement(self):
        """
        compound-statement:
            { block-item-list[opt] }
        """
        z = self.save()
        token = self.curtoken()
        if (
            self.expect(TokenKind.L_BRACE)
            and ((a := self.optional(self.block_item_list)),)
            and self.expect(TokenKind.R_BRACE)
        ):
            return CompoundStmt(items=a, location=token.location)
        self.restore(z)
        return None

    @update_call_tree
    def block_item_list(self):
        """
        block-item-list:
            block-item
            block-item-list block-item
        """
        z = self.save()
        a = []
        b = self.block_item()
        if b == None:
            self.restore(z)
            return None
        a.append(b)
        while self.curtoken().kind != TokenKind.R_BRACE:
            if b := self.block_item():
                a.append(b)
            else:
                self.restore(z)
                return None
        return a

    @update_call_tree
    def block_item(self):
        """
        block-item:
            declaration
            unlabeled-statement
            label
        """
        z = self.save()
        if a := self.declaration():
            return a
        self.restore(z)
        if a := self.unlabeled_statement():
            return a
        self.restore(z)
        if a := self.label():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def expression_statement(self):
        """
        expression-statement:
            expression[opt] ;
            attribute-specifier-sequence expression ;
        """
        z = self.save()
        token = self.curtoken()
        if (
            (a := self.attribute_specifier_sequence())
            and (b := self.expression())
            and self.expect(TokenKind.SEMI)
        ):
            return ExpressionStmt(
                attribute_specifiers=a, expr=b, location=token.location
            )
        self.restore(z)
        if ((a := self.optional(self.expression)),) and self.expect(TokenKind.SEMI):
            return ExpressionStmt(expr=a, location=token.location)
        self.restore(z)
        return None

    @update_call_tree
    def selection_statement(self) -> Stmt:
        """
        selection-statement:
            if ( expression ) secondary-block
            if ( expression ) secondary-block else secondary-block
            switch ( expression ) secondary-block
        """
        z = self.save()
        if (
            (a := self.expect(TokenKind.IF))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.expression())
            and self.expect(TokenKind.R_PAREN)
            and (c := self.secondary_block())
            and self.expect(TokenKind.ELSE)
            and (d := self.secondary_block())
        ):
            return IfStmt(
                condition_expr=b,
                body=c,
                else_body=d,
                location=a.location,
            )
        self.restore(z)
        if (
            (a := self.expect(TokenKind.IF))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.expression())
            and self.expect(TokenKind.R_PAREN)
            and (c := self.secondary_block())
        ):
            return IfStmt(
                condition_expr=b,
                body=c,
                else_body=None,
                location=a.location,
            )
        self.restore(z)
        if (
            (a := self.expect(TokenKind.SWITCH))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.expression())
            and self.expect(TokenKind.R_PAREN)
            and (c := self.secondary_block())
        ):
            return SwitchStmt(
                condition_expr=b,
                body=c,
                location=a.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def iteration_statement(self) -> Stmt:
        """
        iteration-statement:
            while ( expression ) secondary-block
            do secondary-block while ( expression ) ;
            for ( expression[opt] ; expression[opt] ; expression[opt] ) secondary-block
            for ( declaration expression[opt] ; expression[opt] ) secondary-block
        """
        z = self.save()
        if (
            (a := self.expect(TokenKind.WHILE))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.expression())
            and self.expect(TokenKind.R_PAREN)
            and (c := self.secondary_block())
        ):
            return WhileStmt(
                condition_expr=b,
                body=c,
                location=a.location,
            )
        self.restore(z)
        if (
            (a := self.expect(TokenKind.DO))
            and (c := self.secondary_block())
            and self.expect(TokenKind.WHILE)
            and self.expect(TokenKind.L_PAREN)
            and (b := self.expression())
            and self.expect(TokenKind.R_PAREN)
            and self.expect(TokenKind.SEMI)
        ):
            return DoWhileStmt(
                condition_expr=b,
                body=c,
                location=a.location,
            )
        self.restore(z)
        if (
            (a := self.expect(TokenKind.FOR))
            and self.expect(TokenKind.L_PAREN)
            and (b := self.declaration())
            and ((c := self.optional(self.expression)),)
            and self.expect(TokenKind.SEMI)
            and ((d := self.optional(self.expression)),)
            and self.expect(TokenKind.R_PAREN)
            and (e := self.secondary_block())
        ):
            return ForStmt(
                init_decl=b,
                condition_expr=c,
                increase_expr=d,
                body=e,
                location=a.location,
            )
        self.restore(z)
        if (
            (a := self.expect(TokenKind.FOR))
            and self.expect(TokenKind.L_PAREN)
            and ((b := self.optional(self.expression)),)
            and self.expect(TokenKind.SEMI)
            and ((c := self.optional(self.expression)),)
            and self.expect(TokenKind.SEMI)
            and ((d := self.optional(self.expression)),)
            and self.expect(TokenKind.R_PAREN)
            and (e := self.secondary_block())
        ):
            return ForStmt(
                init_expr=b,
                condition_expr=c,
                increase_expr=d,
                body=e,
                location=a.location,
            )
        self.restore(z)
        return None

    @update_call_tree
    def jump_statement(self) -> Stmt:
        """
        jump-statement:
            goto identifier ;
            continue ;
            break ;
            return expression[opt] ;
        """
        z = self.save()
        if (
            (a := self.expect(TokenKind.GOTO))
            and (b := self.expect(TokenKind.IDENTIFIER))
            and self.expect(TokenKind.SEMI)
        ):
            return GotoStmt(name=b.text, location=a.location)
        self.restore(z)
        if a := self.expect(TokenKind.CONTINUE) and self.expect(TokenKind.SEMI):
            return ContinueStmt(location=a.location)
        self.restore(z)
        if a := self.expect(TokenKind.BREAK) and self.expect(TokenKind.SEMI):
            return BreakStmt(location=a.location)
        self.restore(z)
        if (
            (a := self.expect(TokenKind.RETURN))
            and ((b := self.optional(self.expression)),)
            and self.expect(TokenKind.SEMI)
        ):
            return ReturnStmt(expr=b, location=a.location)
        self.restore(z)
        return None

    @update_call_tree
    def translation_unit(self):
        """
        translation-unit:
            external-declaration
            translation-unit external-declaration
        """
        z = self.save()
        a = []
        b = self.external_declaration()
        if b == None:
            self.restore(z)
            return None
        a.append(b)
        z = self.save()
        while b := self.external_declaration():
            a.append(b)
            z = self.save()
        self.restore(z)
        return a

    @update_call_tree
    def external_declaration(self):
        """
        external-declaration:
            function-definition
            declaration
        """
        z = self.save()
        if a := self.function_definition():
            return a
        self.restore(z)
        if a := self.declaration():
            return a
        self.restore(z)
        return None

    @update_call_tree
    def function_definition(self):
        """
        function-definition:
            attribute-specifier-sequence[opt] declaration-specifiers declarator function-body
        function-body:
            compound-statement
        """
        z = self.save()
        token = self.curtoken()
        if (
            ((a := self.optional(self.attribute_specifier_sequence)),)
            and (b := self.declaration_specifiers())
            and (c := self.declarator())
            and (d := self.compound_statement())
        ):
            return FunctionDef(
                attribute_specifiers=a,
                specifiers=b[0],
                specifier_attributes=b[1],
                declarator=c,
                body=d,
                location=token.location,
            )
        self.restore(z)
        return None

    def start(self) -> Node:
        self.nexttoken()

        z = self.save()
        token = self.curtoken()
        if (a := self.translation_unit()) != None:
            return TranslationUnit(body=a, location=token.location)
        self.restore(z)
        return None
