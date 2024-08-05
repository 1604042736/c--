#include <stdarg.h>
#include <stdlib.h>

#include "error.h"
#include "parser.h"
#include "stringutil.h"

Parser *parser_new() { return (Parser *)malloc(sizeof(Parser)); }

void parser_init(Parser *self, Lexer *lexer)
{
    self->lexer = lexer;
    lexer_gettoken(lexer);
}

int parser_match(Parser *self, TokenType actual, TokenType expected)
{
    if (actual != expected) return 0;
    lexer_gettoken(self->lexer);
    return 1;
}

/*下面的这些宏都是跟上下文有关的*/

#define NEWCONTEXT(c)                                                          \
    ASTContext c;                                                              \
    c.filename = self->lexer->token->context.filename;                         \
    c.line = self->lexer->token->context.line;                                 \
    c.s_row = self->lexer->token->context.row;                                 \
    c.s_col = self->lexer->token->context.col;                                 \
    c.e_row = context.s_row;                                                   \
    c.e_col = context.s_col;

#define UPDATECONTEXT(c)                                                       \
    do                                                                         \
    {                                                                          \
        c.e_row = self->lexer->token->context.row;                             \
        c.e_col = self->lexer->token->context.col;                             \
    } while (0)

#define TOKEN self->lexer->token

#define NEWAST(ast, type, context)                                             \
    do                                                                         \
    {                                                                          \
        ast = ast_new();                                                       \
        ast_init(ast, type, context);                                          \
    } while (0)

#define MATCH(expected)                                                        \
    do                                                                         \
    {                                                                          \
        if (!parser_match(self, TOKEN->type, expected))                        \
        {                                                                      \
            LOAD(tk);                                                          \
            return NULL;                                                       \
        }                                                                      \
    } while (0)

#define NONTERMINAL(t, f)                                                      \
    do                                                                         \
    {                                                                          \
        t = f;                                                                 \
        if (t == NULL)                                                         \
        {                                                                      \
            LOAD(tk);                                                          \
            return NULL;                                                       \
        }                                                                      \
    } while (0)

#define STORE(tk) Token *tk = TOKEN
#define LOAD(tk) TOKEN = tk

/*
primary_expression:
    identifier
    | constant
    | string_literal
    | ( expression )
*/
AST *parser_primary_expression(Parser *self)
{
    NEWCONTEXT(context);
    AST *ast = NULL;
    STORE(tk);
    switch (TOKEN->type)
    {
    case TK_NAME:
        NEWAST(ast, AT_NAME, context);
        ast->val = TOKEN->str;
        MATCH(TK_NAME);
        break;
    case TK_INTCONST:
        NEWAST(ast, AT_INTEGER, context);
        ast->val = TOKEN->str;
        MATCH(TK_INTCONST);
        break;
    case TK_FLOATCONST:
        NEWAST(ast, AT_FLOAT, context);
        ast->val = TOKEN->str;
        MATCH(TK_FLOATCONST);
        break;
    case TK_STRINGCONST:
        NEWAST(ast, AT_STRING, context);
        ast->val = TOKEN->str;
        MATCH(TK_STRINGCONST);
        break;
    case TK_LPAREN:
        MATCH(TK_LPAREN);
        NONTERMINAL(ast, parser_expression(self));
        MATCH(TK_RPAREN);
        break;
    }
    return ast;
}

/*
postfix_expression:
    primary_expression
    | postfix_expression '[' expression ']'
    | postfix_expression ([argument_expression_list])
    | postfix_expression . identifier
    | postfix_expression -> identifier
    | postfix_expression ++
    | postfix_expression --
*/
AST *parser_postfix_expression(Parser *self)
{
    NEWCONTEXT(context);
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_primary_expression(self));
    while (TOKEN->type == TK_LSQUARE || TOKEN->type == TK_LPAREN
           || TOKEN->type == TK_PERIOD || TOKEN->type == TK_ARROW
           || TOKEN->type == TK_PLUSPLUS || TOKEN->type == TK_MINUSMINUS)
    {
        AST *t;
        if (TOKEN->type == TK_LSQUARE)
        {
            MATCH(TK_LSQUARE);

            NEWAST(t, AT_SUBSCRIPT, ast->context);
            t->subscript_target = ast;
            NONTERMINAL(t->subscript_index, parser_expression(self));

            MATCH(TK_RSQUARE);
        }
        else if (TOKEN->type == TK_LPAREN)
        {
            MATCH(TK_LPAREN);

            NEWAST(t, AT_CALL, ast->context);
            t->call_func = ast;
            if (TOKEN->type != TK_RPAREN)
                NONTERMINAL(t->call_args,
                            parser_argument_expression_list(self));

            MATCH(TK_RPAREN);
        }
        else if (TOKEN->type == TK_PERIOD || TOKEN->type == TK_ARROW)
        {
            MATCH(TOKEN->type);

            NEWAST(t, AT_MEMBER, ast->context);
            t->member_target = ast;
            t->val = TOKEN->str;
            if (TOKEN->type == TK_ARROW) t->flags |= FLAG_ARROW;

            MATCH(TK_NAME);
        }
        else if (TOKEN->type == TK_PLUSPLUS)
        {
            MATCH(TK_PLUSPLUS);

            NEWAST(t, AT_UNARYOPERATOR, ast->context);
            t->unaryop_operand = ast;
            t->val = "++";
            t->flags |= FLAG_POSTFIX;
        }
        else if (TOKEN->type == TK_MINUSMINUS)
        {
            MATCH(TK_MINUSMINUS);

            NEWAST(t, AT_UNARYOPERATOR, ast->context);
            t->unaryop_operand = ast;
            t->val = "--";
            t->flags |= FLAG_POSTFIX;
        }
        UPDATECONTEXT(t->context);
        ast = t;
    }
    UPDATECONTEXT(ast->context);
    return ast;
}

/*
argument_expression_list:
    assignment_expression
    | assignmant_expression_list , assignment_expression
*/
AST *parser_argument_expression_list(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_assignment_expression(self));
    AST *p = ast;
    while (TOKEN->type == TK_COMMA)
    {
        MATCH(TK_COMMA);
        NONTERMINAL(p->sibling, parser_assignment_expression(self));
        p = p->sibling;
        p->head_sibling = ast;
    }
    return ast;
}

/*
unary_expression:
    postfix_expression
    | ++ unary_expression
    | -- unary_expression
    | unary_operator cast_expression
    | sizeof unary_expression
    | sizeof (type_name)

unary_operator:
    & * + - ~ !
*/
AST *parser_unary_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NEWCONTEXT(context);
    if (TOKEN->type == TK_PLUSPLUS || TOKEN->type == TK_MINUSMINUS)
    {
        NEWAST(ast, AT_UNARYOPERATOR, context);
        ast->val = TOKEN->str;
        ast->flags |= FLAG_PREFIX;
        MATCH(TOKEN->type);
        NONTERMINAL(ast->unaryop_operand, parser_unary_expression(self));
        NONTERMINAL(ast->unaryop_operand, parser_unary_expression(self));
    }
    else if (TOKEN->type == TK_SIZEOF)
    {
        NEWAST(ast, AT_UNARYOPERATOR, context);
        ast->val = "sizeof";
        MATCH(TK_SIZEOF);
        if (TOKEN->type == TK_LPAREN)
        {
            MATCH(TK_LPAREN);
            NONTERMINAL(ast->unaryop_operand, parser_type_name(self));
            MATCH(TK_RPAREN);
        }
        else
            NONTERMINAL(ast->unaryop_operand, parser_unary_expression(self));
    }
    else if (TOKEN->type == TK_AMP || TOKEN->type == TK_STAR
             || TOKEN->type == TK_PLUS || TOKEN->type == TK_MINUS
             || TOKEN->type == TK_TILDE || TOKEN->type == TK_EXCLAIM)
    {
        NEWAST(ast, AT_UNARYOPERATOR, context);
        ast->val = TOKEN->str;
        MATCH(TOKEN->type);
        NONTERMINAL(ast->unaryop_operand, parser_cast_expression(self));
    }
    else
        NONTERMINAL(ast, parser_postfix_expression(self));
    UPDATECONTEXT(ast->context);
    return ast;
}

/*
cast_expression:
    unary_expression
    | (type_name) cast_expression
*/
AST *parser_cast_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    if (TOKEN->type == TK_LPAREN)
    {
        NEWCONTEXT(context);
        NEWAST(ast, AT_CAST, context);

        MATCH(TK_LPAREN);
        NONTERMINAL(ast->cast_type, parser_type_name(self));
        MATCH(TK_RPAREN);
        NONTERMINAL(ast->cast_target, parser_cast_expression(self));

        UPDATECONTEXT(ast->context);
    }
    else
        NONTERMINAL(ast, parser_unary_expression(self));
    return ast;
}

/*
multiplicative_expression:
    cast_expression
    | multiplicative_expression * cast_expression
    | multiplicative_expression / cast_expression
    | multiplicative_expression % cast_expression
*/
AST *parser_multiplicative_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_cast_expression(self));
    while (TOKEN->type == TK_STAR || TOKEN->type == TK_SLASH
           || TOKEN->type == TK_PERCENT)
    {
        AST *t;
        NEWAST(t, AT_BINARYOPERATOR, ast->context);
        t->val = TOKEN->str;
        t->binop_left = ast;
        MATCH(TOKEN->type);
        NONTERMINAL(t->binop_right, parser_cast_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
addtive_expression:
    multiplicative_expression
    | addtive_expression + multiplicative_expression
    | addtive_expression - multiplicative_expression
*/
AST *parser_addtive_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_multiplicative_expression(self));
    while (TOKEN->type == TK_PLUS || TOKEN->type == TK_MINUS)
    {
        AST *t;
        NEWAST(t, AT_BINARYOPERATOR, ast->context);
        t->val = TOKEN->str;
        t->binop_left = ast;
        MATCH(TOKEN->type);
        NONTERMINAL(t->binop_right, parser_multiplicative_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
shift_expression:
    addtive_expression
    | shift_expression << addtive_expression
    | shift_expression >> addtive_expression
*/
AST *parser_shift_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_addtive_expression(self));
    while (TOKEN->type == TK_GREATERGREATER || TOKEN->type == TK_LESSLESS)
    {
        AST *t;
        NEWAST(t, AT_BINARYOPERATOR, ast->context);
        t->val = TOKEN->str;
        t->binop_left = ast;
        MATCH(TOKEN->type);
        NONTERMINAL(t->binop_right, parser_addtive_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
relational_expression:
    shift_expression
    | relational_expression < shift_expression
    | relational_expression <= shift_expression
    | relational_expression > shift_expression
    | relational_expression >= shift_expression
*/
AST *parser_relational_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_shift_expression(self));
    while (TOKEN->type == TK_GREATER || TOKEN->type == TK_GREATEREQUAL
           || TOKEN->type == TK_LESS || TOKEN->type == TK_LESSEQUAL)
    {
        AST *t;
        NEWAST(t, AT_BINARYOPERATOR, ast->context);
        t->val = TOKEN->str;
        t->binop_left = ast;
        MATCH(TOKEN->type);
        NONTERMINAL(t->binop_right, parser_shift_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
equality_expression:
    relational_expression
    | equality_expression == relational_expression
    | equality_expression != relational_expression
*/
AST *parser_equality_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_relational_expression(self));
    while (TOKEN->type == TK_EQUALEQUAL || TOKEN->type == TK_EXCLAIMEQUAL)
    {
        AST *t;
        NEWAST(t, AT_BINARYOPERATOR, ast->context);
        t->val = TOKEN->str;
        t->binop_left = ast;
        MATCH(TOKEN->type);
        NONTERMINAL(t->binop_right, parser_relational_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
and_expression:
    equality_expression
    | and_expression & relational_expression
*/
AST *parser_and_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_equality_expression(self));
    while (TOKEN->type == TK_AMP)
    {
        AST *t;
        NEWAST(t, AT_BINARYOPERATOR, ast->context);
        t->val = TOKEN->str;
        t->binop_left = ast;
        MATCH(TOKEN->type);
        NONTERMINAL(t->binop_right, parser_equality_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
exclusive_or_expression:
    and_expression
    | exclusive_or_expression ^ and_expression
*/
AST *parser_exclusive_or_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_and_expression(self));
    while (TOKEN->type == TK_CARET)
    {
        AST *t;
        NEWAST(t, AT_BINARYOPERATOR, ast->context);
        t->val = TOKEN->str;
        t->binop_left = ast;
        MATCH(TOKEN->type);
        NONTERMINAL(t->binop_right, parser_and_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
inclusive_or_expression:
    exclusive_or_expression
    | inclusive_or_expression | exclusive_or_expression
*/
AST *parser_inclusive_or_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_exclusive_or_expression(self));
    while (TOKEN->type == TK_PIPE)
    {
        AST *t;
        NEWAST(t, AT_BINARYOPERATOR, ast->context);
        t->val = TOKEN->str;
        t->binop_left = ast;
        MATCH(TOKEN->type);
        NONTERMINAL(t->binop_right, parser_exclusive_or_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
logical_and_expression:
    inclusive_or_expression
    | logical_and_expression && inclusive_or_expression
*/
AST *parser_logical_and_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_inclusive_or_expression(self));
    while (TOKEN->type == TK_AMPAMP)
    {
        AST *t;
        NEWAST(t, AT_BINARYOPERATOR, ast->context);
        t->val = TOKEN->str;
        t->binop_left = ast;
        MATCH(TOKEN->type);
        NONTERMINAL(t->binop_right, parser_inclusive_or_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
logical_or_expression:
    logical_and_expression
    | logical_or_expression || logical_and_expression
*/
AST *parser_logical_or_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_logical_and_expression(self));
    while (TOKEN->type == TK_PIPEPIPE)
    {
        AST *t;
        NEWAST(t, AT_BINARYOPERATOR, ast->context);
        t->val = TOKEN->str;
        t->binop_left = ast;
        MATCH(TOKEN->type);
        NONTERMINAL(t->binop_right, parser_logical_and_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
conditional_expression:
    logical_or_expression 
    | logical_or_expression ? expression : conditional_expression
*/
AST *parser_conditional_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_logical_or_expression(self));
    if (TOKEN->type == TK_QUESTION)
    {
        AST *t;
        NEWAST(t, AT_CONDITIONALOPERATOR, ast->context);
        t->condop_cond = ast;
        MATCH(TK_QUESTION);
        NONTERMINAL(t->condop_true, parser_expression(self));
        MATCH(TK_COLON);
        NONTERMINAL(t->condop_false, parser_conditional_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
assignment_expression:
    conditional_expression
    | unary_expression assignment_operator assignment_expression

assignment_operator:
    = *= /= %= += -= <<= >>= &= ^= |=
*/
AST *parser_assignment_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_conditional_expression(self));
    if (TOKEN->type == TK_EQUAL || TOKEN->type == TK_STAREQUAL
        || TOKEN->type == TK_SLASHEQUAL || TOKEN->type == TK_PERCENTEQUAL
        || TOKEN->type == TK_PLUSEQUAL || TOKEN->type == TK_MINUSEQUAL
        || TOKEN->type == TK_LESSLESSEQUAL
        || TOKEN->type == TK_GREATERGREATEREQUAL || TOKEN->type == TK_AMPEQUAL
        || TOKEN->type == TK_CARETEQUAL || TOKEN->type == TK_PIPEEQUAL)
    {
        AST *t;
        NEWAST(t, AT_BINARYOPERATOR, ast->context);
        t->val = TOKEN->str;
        t->binop_left = ast;
        MATCH(TOKEN->type);
        NONTERMINAL(t->binop_right, parser_assignment_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
expression:
    assignment_expression
    | expression , assignment_expression
*/
AST *parser_expression(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_assignment_expression(self));
    while (TOKEN->type == TK_COMMA)
    {
        AST *t;
        NEWAST(t, AT_BINARYOPERATOR, ast->context);
        t->val = TOKEN->str;
        t->binop_left = ast;
        MATCH(TOKEN->type);
        NONTERMINAL(t->binop_right, parser_assignment_expression(self));
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
constant_expression:
    conditional_expression
*/
AST *parser_constant_expression(Parser *self)
{
    return parser_conditional_expression(self);
}

/*
declaration:
    declaration_specifier [init_declaratior_list] ;
*/
AST *parser_declaration(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    NEWAST(ast, AT_DECLSTMT, context);
    NONTERMINAL(ast->decl_spec, parser_declaration_specifier(self));
    if (TOKEN->type != TK_SEMI)
        NONTERMINAL(ast->decl_declor, parser_init_declaratior_list(self));
    UPDATECONTEXT(ast->context);
    MATCH(TK_SEMI);
    return ast;
}
int parser_is_declaration(Parser *self)
{
    return parser_is_storage_class_specifier(self)
           || parser_is_type_qualifier(self) || parser_is_type_specifer(self);
}

/*declaration_specifier:
    storage_class_specifier [declaration_specifier]
    | type_specifer [declaration_specifier]
    | type_qualifier [declaration_specifier]
*/
AST *parser_declaration_specifier(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    int type_specifer_matched = 0;
    int combinable = 0;
    if (parser_is_storage_class_specifier(self))
        NONTERMINAL(ast, parser_storage_class_specifier(self));
    else if (parser_is_type_specifer(self))
    {
        type_specifer_matched = 1;
        combinable = TOKEN->type != TK_NAME; // typdef_name组合无意义
        NONTERMINAL(ast, parser_type_specifer(self));
    }
    else if (parser_is_type_qualifier(self))
        NONTERMINAL(ast, parser_type_qualifier(self));
    AST *p = ast;
    while (parser_is_storage_class_specifier(self)
           || parser_is_type_specifer(self) || parser_is_type_qualifier(self))
    {
        if (parser_is_storage_class_specifier(self))
            NONTERMINAL(p->sibling, parser_storage_class_specifier(self));
        else if (parser_is_type_specifer(self))
        {
            if (type_specifer_matched && !combinable) break;
            if (type_specifer_matched && combinable
                && TOKEN->type == TK_NAME) // typdef_name组合无意义
                break;
            type_specifer_matched = 1;
            combinable = TOKEN->type != TK_NAME;
            NONTERMINAL(p->sibling, parser_type_specifer(self));
        }
        else if (parser_is_type_qualifier(self))
            NONTERMINAL(p->sibling, parser_type_qualifier(self));
        p = p->sibling;
        p->head_sibling = ast;
    }
    return ast;
}

/*init_declaratior_list:
    init_declarator
    | init_declaratior_list , init_declarator
*/
AST *parser_init_declaratior_list(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_init_declarator(self));
    AST *p = ast;
    while (TOKEN->type == TK_COMMA)
    {
        MATCH(TK_COMMA);
        NONTERMINAL(p->sibling, parser_init_declarator(self));
        p = p->sibling;
        p->head_sibling = ast;
    }
    return ast;
}

/*init_declarator:
    declarator
    | declarator = initializer
*/
AST *parser_init_declarator(Parser *self)
{
    NEWCONTEXT(context);
    STORE(tk);
    AST *ast;
    NEWAST(ast, AT_INITDECLARATOR, context);
    NONTERMINAL(ast->initdecl_decl, parser_declarator(self));
    if (TOKEN->type == TK_EQUAL)
    {
        MATCH(TK_EQUAL);
        NONTERMINAL(ast->initdecl_init, parser_initializer(self));
    }
    UPDATECONTEXT(context);
    return ast;
}

/*
storage_class_specifier:
    typedef
    | extern
    | static
    | auto
    | register
*/
AST *parser_storage_class_specifier(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    NEWAST(ast, AT_STORAGECLASSSPECIFIER, context);
    ast->val = TOKEN->str;
    MATCH(TOKEN->type);
    return ast;
}
int parser_is_storage_class_specifier(Parser *self)
{
    return TOKEN->type == TK_TYPEDEF || TOKEN->type == TK_EXTERN
           || TOKEN->type == TK_STATIC || TOKEN->type == TK_AUTO
           || TOKEN->type == TK_REGISTER;
}

/*
type_specifer:
    void
    | char
    | short
    | int
    | long
    | float
    | double
    | signed
    | unsigned
    | struct_or_union_specifer
    | enum_specifier
    | typedef_name

typedef_name:
    identifier
*/
AST *parser_type_specifer(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast = NULL;
    if (TOKEN->type == TK_STRUCT || TOKEN->type == TK_UNION)
        NONTERMINAL(ast, parser_struct_or_union_specifer(self));
    else if (TOKEN->type == TK_ENUM)
        NONTERMINAL(ast, parser_enum_specifier(self));
    else
    {
        NEWAST(ast, AT_TYPESPECIFER, context);
        ast->val = TOKEN->str;
        MATCH(TOKEN->type);
    }
    return ast;
}
int parser_is_type_specifer(Parser *self)
{
    return TOKEN->type == TK_VOID || TOKEN->type == TK_CHAR
           || TOKEN->type == TK_SHORT || TOKEN->type == TK_INT
           || TOKEN->type == TK_LONG || TOKEN->type == TK_FLOAT
           || TOKEN->type == TK_DOUBLE || TOKEN->type == TK_SIGNED
           || TOKEN->type == TK_SIGNED || TOKEN->type == TK_UNSIGNED
           || TOKEN->type == TK_STRUCT || TOKEN->type == TK_UNION
           || TOKEN->type == TK_ENUM || TOKEN->type == TK_NAME;
}

/*
struct_or_union_specifer:
    struct_or_union [identifier] { struct_declaration_list}
    | struct_or_union identifier

struct_or_union:
    struct
    | union
*/
AST *parser_struct_or_union_specifer(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast = NULL;
    if (TOKEN->type == TK_STRUCT)
    {
        NEWAST(ast, AT_STRUCTSPECIFIER, context);
        MATCH(TK_STRUCT);
    }
    else if (TOKEN->type == TK_UNION)
    {
        NEWAST(ast, AT_UNIONSPECIFIER, context);
        MATCH(TK_UNION);
    }
    if (TOKEN->type == TK_NAME)
    {
        ast->val = TOKEN->str;
        MATCH(TK_NAME);
    }
    if (TOKEN->type == TK_LBRACE)
    {
        MATCH(TK_LBRACE);
        NONTERMINAL(ast->souspec_list, parser_struct_declaration_list(self));
        MATCH(TK_RBRACE);
    }
    UPDATECONTEXT(ast->context);
    return ast;
}

/*
struct_declaration_list:
    struct_declaration
    | struct_declaration_list struct_declaration
*/
AST *parser_struct_declaration_list(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_struct_declaration(self));
    AST *p = ast;
    while (TOKEN->type != TK_RBRACE)
    {
        NONTERMINAL(p->sibling, parser_struct_declaration(self));
        p = p->sibling;
        p->head_sibling = ast;
    }
    return ast;
}

/*
struct_declaration:
    specifier_qualifier_list struct_declarator_list;
*/
AST *parser_struct_declaration(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    NEWAST(ast, AT_FIELDDECLARATION, context);
    NONTERMINAL(ast->decl_spec, parser_specifier_qualifier_list(self));
    NONTERMINAL(ast->decl_declor, parser_struct_declarator_list(self));
    UPDATECONTEXT(ast->context);
    MATCH(TK_SEMI);
    return ast;
}

/*
specifier_qualifier_list:
    type_specifer [specifier_qualifier_list]
    | type_qualifier [specifier_qualifier_list]
*/
AST *parser_specifier_qualifier_list(Parser *self)
{
    STORE(tk);
    AST *ast;
    int type_specifer_matched = 0;
    int combinable = 0;
    if (parser_is_type_specifer(self))
    {
        type_specifer_matched = 1;
        combinable = TOKEN->type != TK_NAME;
        NONTERMINAL(ast, parser_type_specifer(self));
    }
    else if (parser_is_type_qualifier(self))
        NONTERMINAL(ast, parser_type_qualifier(self));
    AST *p = ast;
    while (parser_is_type_specifer(self) || parser_is_type_qualifier(self))
    {
        if (parser_is_type_specifer(self))
        {
            if (type_specifer_matched && !combinable) break;
            if (type_specifer_matched && combinable && TOKEN->type == TK_NAME)
                break;
            type_specifer_matched = 1;
            combinable = TOKEN->type != TK_NAME;
            NONTERMINAL(p->sibling, parser_type_specifer(self));
        }
        else if (parser_is_type_qualifier(self))
            NONTERMINAL(p->sibling, parser_type_qualifier(self));
        p = p->sibling;
        p->head_sibling = ast;
    }
    return ast;
}

/*
struct_declarator_list:
    struct_declarator
    | struct_declarator_list, struct_declarator
*/
AST *parser_struct_declarator_list(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_struct_declarator(self));
    AST *p = ast;
    while (TOKEN->type == TK_COMMA)
    {
        MATCH(TK_COMMA);
        NONTERMINAL(p->sibling, parser_struct_declarator(self));
        p = p->sibling;
        p->head_sibling = ast;
    }
    return ast;
}

/*
struct_declarator:
    declarator
    | [declarator] : constant_expression
*/
AST *parser_struct_declarator(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    NEWAST(ast, AT_STRUCTDECLARATOR, context);
    if (TOKEN->type != TK_COLON)
        NONTERMINAL(ast->structdeclor_declor, parser_declarator(self));
    if (TOKEN->type == TK_COLON)
    {
        MATCH(TK_COLON);
        NONTERMINAL(ast->structdeclor_const, parser_constant_expression(self));
    }
    UPDATECONTEXT(ast->context);
    return ast;
}

/*
enum_specifier:
    enum [identifier] {enumerator_list}
    | enum identifier
*/
AST *parser_enum_specifier(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    NEWAST(ast, AT_ENUMSPECIFIER, context);
    MATCH(TK_ENUM);
    if (TOKEN->type == TK_NAME)
    {
        ast->val = TOKEN->str;
        MATCH(TK_NAME);
    }
    if (TOKEN->type == TK_LBRACE)
    {
        MATCH(TK_LBRACE);
        NONTERMINAL(ast->enum_enumor, parser_enumerator_list(self));
        MATCH(TK_RBRACE);
    }
    UPDATECONTEXT(ast->context);
    return ast;
}

/*
enumerator_list:
    enumerator
    | enumerator_list, enumerator
*/
AST *parser_enumerator_list(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_enumerator(self));
    AST *p = ast;
    while (TOKEN->type == TK_COMMA)
    {
        MATCH(TK_COMMA);
        NONTERMINAL(p->sibling, parser_enumerator(self));
        p = p->sibling;
        p->head_sibling = ast;
    }
    return ast;
}

/*
enumerator:
    enumeration_constant
    | enumeration_constant = constant_expression

enumeration_constant:
    identifier
*/
AST *parser_enumerator(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    NEWAST(ast, AT_ENUMERATOR, context);
    ast->val = TOKEN->str;
    MATCH(TK_NAME);
    if (TOKEN->type == TK_EQUAL)
    {
        MATCH(TK_EQUAL);
        NONTERMINAL(ast->enumor_const, parser_constant_expression(self));
    }
    UPDATECONTEXT(ast->context);
    return ast;
}

/*
type_qualifier:
    const
    | volatile
*/
AST *parser_type_qualifier(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    NEWAST(ast, AT_TYPEQUALIFIER, context);
    ast->val = TOKEN->str;
    MATCH(TOKEN->type);
    return ast;
}
int parser_is_type_qualifier(Parser *self)
{
    return TOKEN->type == TK_CONST || TOKEN->type == TK_VOLATILE;
}

/*
parameter_declaration:
    declaration_specifier declarator
    | declaration_specifier [abstract_declarator]
*/
AST *parser_parameter_declaration(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    NEWAST(ast, AT_PARAMDECLARATION, context);
    NONTERMINAL(ast->decl_spec, parser_declaration_specifier(self));

    STORE(tk2);
    ast->decl_declor = parser_declarator(self);
    if (ast->decl_declor == NULL)
    {
        LOAD(tk2);
        ast->decl_declor = parser_abstract_declarator(self);
        if (ast->decl_declor == NULL) LOAD(tk2);
    }
    UPDATECONTEXT(ast->context);
    return ast;
}

/*
declarator:
    [pointer] direct_declarator
*/
AST *parser_declarator(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    if (parser_is_pointer(self)) NONTERMINAL(ast, parser_pointer(self));
    if (ast != NULL)
        NONTERMINAL(ast->pdeclor_sub, parser_direct_declarator(self));
    else
        NONTERMINAL(ast, parser_direct_declarator(self));
    UPDATECONTEXT(ast->context);
    return ast;
}

/*
abstract_declarator:
    pointer
    | [pointer] direct_abstract_delarator
*/
AST *parser_abstract_declarator(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    if (parser_is_pointer(self))
    {
        NONTERMINAL(ast, parser_pointer(self));
        STORE(tk);
        AST *t = NULL;
        t = parser_direct_abstract_delarator(self);
        if (t == NULL) LOAD(tk);
        ast->pdeclor_sub = t;
    }
    else
        NONTERMINAL(ast, parser_direct_abstract_delarator(self));
    UPDATECONTEXT(ast->context);
    return ast;
}

/*
direct_declarator:
    identifier
    | (declarator)
    | direct_declarator '[' [ constant_expression ] ']'
    | direct_declarator (parameter_type_list)
    | direct_declarator ( [identifier_list] )
*/
AST *parser_direct_declarator(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    if (TOKEN->type == TK_NAME)
    {
        NEWAST(ast, AT_NAME, context);
        ast->val = TOKEN->str;
        MATCH(TK_NAME);
    }
    else if (TOKEN->type == TK_LPAREN)
    {
        MATCH(TK_LPAREN);
        NONTERMINAL(ast, parser_declarator(self));
        MATCH(TK_RPAREN);
    }
    else
        return NULL;
    while (TOKEN->type == TK_LSQUARE || TOKEN->type == TK_LPAREN)
    {
        AST *t;
        if (TOKEN->type == TK_LSQUARE)
        {
            MATCH(TK_LSQUARE);
            NEWAST(t, AT_ARRAYDECLARATOR, ast->context);
            t->arraydeclor_sub = ast;
            if (TOKEN->type != TK_RSQUARE)
                NONTERMINAL(t->arraydeclor_len,
                            parser_constant_expression(self));
            MATCH(TK_RSQUARE);
        }
        else if (TOKEN->type == TK_LPAREN)
        {
            // 这里与文法描述不符 [identifier_list]
            MATCH(TK_LPAREN);
            NEWAST(t, AT_FUNCTIONDECLARATOR, ast->context);
            t->funcdeclor_sub = ast;
            if (TOKEN->type != TK_RPAREN)
                NONTERMINAL(t->funcdeclor_param,
                            parser_parameter_type_list(self));
            MATCH(TK_RPAREN);
        }
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
direct_abstract_delarator:
   (abstract_declarator)
   | [direct_abstract_delarator] '[' [constant_expression] ']'
   | [direct_abstract_delarator] ( [parameter_type_list] )
*/
AST *parser_direct_abstract_delarator(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    if (TOKEN->type == TK_LPAREN)
    {
        MATCH(TK_LPAREN);
        if (parser_is_pointer(self) || TOKEN->type == TK_LSQUARE
            || TOKEN->type == TK_LPAREN)
            NONTERMINAL(ast, parser_abstract_declarator(self));
        else // 不等价
            NEWAST(ast, AT_FUNCTIONDECLARATOR, context);
        MATCH(TK_RPAREN);
    }
    while (TOKEN->type == TK_LSQUARE || TOKEN->type == TK_LPAREN)
    {
        AST *t;
        if (TOKEN->type == TK_LSQUARE)
        {
            MATCH(TK_LSQUARE);
            NEWAST(t, AT_ARRAYDECLARATOR, ast->context);
            t->arraydeclor_sub = ast;
            if (TOKEN->type != TK_RSQUARE)
                NONTERMINAL(t->arraydeclor_len,
                            parser_constant_expression(self));
            MATCH(TK_RSQUARE);
        }
        else if (TOKEN->type == TK_LPAREN)
        {
            MATCH(TK_LPAREN);
            NEWAST(t, AT_FUNCTIONDECLARATOR, ast->context);
            t->funcdeclor_sub = ast;
            if (TOKEN->type != TK_RPAREN)
                NONTERMINAL(t->funcdeclor_param,
                            parser_parameter_type_list(self));
            MATCH(TK_RPAREN);
        }
        UPDATECONTEXT(t->context);
        ast = t;
    }
    return ast;
}

/*
pointer:
    * [type_qualifier_list]
    | * [type_qualifier_list] pointer
*/
AST *parser_pointer(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    NEWAST(ast, AT_POINTERDECLARATOR, context);
    MATCH(TK_STAR);
    if (parser_is_type_qualifier_list(self))
        NONTERMINAL(ast->pdeclor_qualifier, parser_type_qualifier_list(self));
    if (parser_is_pointer(self))
        NONTERMINAL(ast->pdeclor_sub, parser_pointer(self));
    UPDATECONTEXT(ast->context);
    return ast;
}
int parser_is_pointer(Parser *self) { return TOKEN->type == TK_STAR; }

/*
type_qualifier_list:
    type_qualifier
    | type_qualifier_list type_qualifier
*/
AST *parser_type_qualifier_list(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_type_qualifier(self));
    AST *p = ast;
    while (parser_is_type_qualifier(self))
    {
        NONTERMINAL(p->sibling, parser_type_qualifier(self));
        p = p->sibling;
        p->head_sibling = ast;
    }
    return ast;
}
int parser_is_type_qualifier_list(Parser *self)
{
    return parser_is_type_qualifier(self);
}

/*
parameter_type_list:
    parameter_list
    | parameter_list, ...
*/
AST *parser_parameter_type_list(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_parameter_list(self));
    return ast;
}

/*
parameter_list:
    parameter_declaration
    | parameter_list, parameter_declaration
*/
AST *parser_parameter_list(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_parameter_declaration(self));
    AST *p = ast;
    while (TOKEN->type == TK_COMMA)
    {
        MATCH(TK_COMMA);
        NEWCONTEXT(context);
        if (TOKEN->type == TK_ELLIPSIS)
        {
            NEWAST(p->sibling, AT_VARPARAM, context);
            MATCH(TK_ELLIPSIS);
        }
        else
            NONTERMINAL(p->sibling, parser_parameter_declaration(self));
        p = p->sibling;
        p->head_sibling = ast;
    }
    return ast;
}

/*
type_name:
    specifier_qualifier_list [abstract_declarator]
*/
AST *parser_type_name(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    NEWAST(ast, AT_TYPENAME, context);
    NONTERMINAL(ast->typename_specqual, parser_specifier_qualifier_list(self));

    STORE(tk2);
    ast->typename_declor = parser_abstract_declarator(self);
    if (ast->typename_declor == NULL) LOAD(tk2);
    UPDATECONTEXT(ast->context);
    return ast;
}

/*
initializer:
    assignment_expression
    | {initializer_list}
    | {initializer_list,}
*/
AST *parser_initializer(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    if (TOKEN->type == TK_LBRACE)
    {
        NEWAST(ast, AT_INITLIST, context);
        MATCH(TK_LBRACE);
        NONTERMINAL(ast->initlist_list, parser_initializer_list(self));
        UPDATECONTEXT(ast->context);
        MATCH(TK_RBRACE);
    }
    else
        NONTERMINAL(ast, parser_assignment_expression(self));
    return ast;
}

/*
initializer_list:
    initializer
    | initializer_list, initializer
*/
AST *parser_initializer_list(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_initializer(self));
    AST *p = ast;
    while (1)
    {
        MATCH(TK_COMMA);
        if (TOKEN->type == TK_RBRACE) break;
        NONTERMINAL(p->sibling, parser_initializer(self));
        p = p->sibling;
        p->head_sibling = ast;
    }

    return ast;
}

/*
statement:
    labeled_statement
    | compound_statement
    | expression_statement
    | selection_statement
    | iteration_statement
    | jump_statement
*/
AST *parser_statement(Parser *self)
{
    AST *ast = NULL;
    STORE(tk);
    if ((ast = parser_labeled_statement(self)) != NULL) return ast;
    LOAD(tk);
    if (TOKEN->type == TK_LBRACE
        && (ast = parser_compound_statement(self)) != NULL)
        return ast;
    LOAD(tk);
    if ((ast = parser_expression_statement(self)) != NULL) return ast;
    LOAD(tk);
    if ((ast = parser_selection_statement(self)) != NULL) return ast;
    LOAD(tk);
    if ((ast = parser_iteration_statement(self)) != NULL) return ast;
    LOAD(tk);
    if ((ast = parser_jump_statement(self)) != NULL) return ast;
    LOAD(tk);
    return NULL;
}

/*
labeled_statement:
    identifier : [statement]
    | case constant_expression : [statement]
    | default : [statement]
*/
AST *parser_labeled_statement(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast = NULL;
    switch (TOKEN->type)
    {
    case TK_NAME:
        NEWAST(ast, AT_LABEL, context);
        MATCH(TK_NAME);
        MATCH(TK_COLON);
        NONTERMINAL(ast->label_stmt, parser_statement(self));
        UPDATECONTEXT(ast->context);
        break;
    case TK_CASE:
        NEWAST(ast, AT_CASE, context);
        MATCH(TK_CASE);
        NONTERMINAL(ast->case_expr, parser_constant_expression(self));
        MATCH(TK_COLON);
        NONTERMINAL(ast->case_stmt, parser_statement(self));
        UPDATECONTEXT(ast->context);
        break;
    case TK_DEFAULT:
        NEWAST(ast, AT_DEFAULT, context);
        MATCH(TK_COLON);
        NONTERMINAL(ast->default_stmt, parser_statement(self));
        UPDATECONTEXT(context);
        break;
    }
    return ast;
}

/*
compound-statement:
    { [ block-item-list] }

block-item-list:
    block-item
    | block-item-list block-item

block-item:
    declaration
    statement
    labe
*/
AST *parser_compound_statement(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    NEWAST(ast, AT_COMPOUND, context);
    MATCH(TK_LBRACE);
    AST *p = ast->compound_stmt;
    while (TOKEN->type != TK_RBRACE)
    {
        AST *t;
        STORE(tk);
        t = parser_declaration(self);
        if (t == NULL)
        {
            LOAD(tk);
            NONTERMINAL(t, parser_statement(self));
        }
        if (p == NULL)
            ast->compound_stmt = p = t;
        else
        {
            p->sibling = t;
            p = p->sibling;
        }
        while (p->sibling != NULL)
        {
            p->head_sibling = ast;
            p = p->sibling;
        }
    }
    MATCH(TK_RBRACE);
    UPDATECONTEXT(ast->context);
    return ast;
}

/*
declaration_list:
    declaration
    | declaration_list declaration
*/
AST *parser_declaration_list(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    NONTERMINAL(ast, parser_declaration(self));
    AST *p = ast;
    while (parser_is_declaration(self))
    {
        NONTERMINAL(p->sibling, parser_declaration(self));
        p = p->sibling;
        p->head_sibling = ast;
    }
    return ast;
}

/*
expression_statement:
    [expression] ;
*/
AST *parser_expression_statement(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast;
    if (TOKEN->type != TK_SEMI)
        NONTERMINAL(ast, parser_expression(self));
    else
        NEWAST(ast, AT_NULLSTMT, context);
    MATCH(TK_SEMI);
    return ast;
}

/*
selection_statement:
    if(expression) statement
    | if(expression) statement else statement
    | switch(expression) statement
*/
AST *parser_selection_statement(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast = NULL;
    switch (TOKEN->type)
    {
    case TK_IF:
        NEWAST(ast, AT_IF, context);
        MATCH(TK_IF);
        MATCH(TK_LPAREN);
        NONTERMINAL(ast->if_cond, parser_expression(self));
        MATCH(TK_RPAREN);
        NONTERMINAL(ast->if_body, parser_statement(self));
        if (TOKEN->type == TK_ELSE)
        {
            MATCH(TK_ELSE);
            NONTERMINAL(ast->if_else, parser_statement(self));
        }
        UPDATECONTEXT(ast->context);
        break;
    case TK_SWITCH:
        NEWAST(ast, AT_SWITCH, context);
        MATCH(TK_SWITCH);
        MATCH(TK_LPAREN);
        NONTERMINAL(ast->switch_expr, parser_expression(self));
        MATCH(TK_RPAREN);
        NONTERMINAL(ast->switch_body, parser_statement(self));
        UPDATECONTEXT(ast->context);
        MATCH(TK_SEMI);
        break;
    }
    return ast;
}

/*
iteration_statement:
    while(expression) statement
    | do statement while(expression) ;
    | for([expression] ; [expression] ; [expression]) statement
*/
AST *parser_iteration_statement(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast = NULL;
    switch (TOKEN->type)
    {
    case TK_WHILE:
        NEWAST(ast, AT_WHILE, context);
        MATCH(TK_WHILE);
        MATCH(TK_LPAREN);
        NONTERMINAL(ast->while_cond, parser_expression(self));
        MATCH(TK_RPAREN);
        NONTERMINAL(ast->while_body, parser_statement(self));
        UPDATECONTEXT(ast->context);
        break;
    case TK_DO:
        NEWAST(ast, AT_DOWHILE, context);
        MATCH(TK_DO);
        NONTERMINAL(ast->dowhile_body, parser_statement(self));
        MATCH(TK_LPAREN);
        NONTERMINAL(ast->dowhile_cond, parser_expression(self));
        MATCH(TK_RPAREN);
        UPDATECONTEXT(ast->context);
        MATCH(TK_SEMI);
        break;
    case TK_FOR:
        NEWAST(ast, AT_FOR, context);
        MATCH(TK_FOR);
        MATCH(TK_LPAREN);

        if (TOKEN->type != TK_SEMI)
            NONTERMINAL(ast->for_init, parser_expression(self));
        MATCH(TK_SEMI);
        if (TOKEN->type != TK_SEMI)
            NONTERMINAL(ast->for_cond, parser_expression(self));
        MATCH(TK_SEMI);
        if (TOKEN->type != TK_RPAREN)
            NONTERMINAL(ast->for_iter, parser_expression(self));

        MATCH(TK_RPAREN);
        NONTERMINAL(ast->for_body, parser_statement(self));
        UPDATECONTEXT(ast->context);
        break;
    }
    return ast;
}

/*
jump_statement:
    goto identifier ;
    | continue ;
    | break ;
    | return [expression] ;
*/
AST *parser_jump_statement(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast = NULL;
    switch (TOKEN->type)
    {
    case TK_GOTO:
        NEWAST(ast, AT_GOTO, context);
        MATCH(TK_GOTO);
        ast->val = TOKEN->str;
        MATCH(TK_NAME);
        UPDATECONTEXT(ast->context);
        MATCH(TK_SEMI);
        break;
    case TK_CONTINUE:
        NEWAST(ast, AT_CONTINUE, context);
        MATCH(TK_SEMI);
        break;
    case TK_BREAK:
        NEWAST(ast, AT_BREAK, context);
        MATCH(TK_SEMI);
        break;
    case TK_RETURN:
        NEWAST(ast, AT_RETURN, context);
        MATCH(TK_RETURN);
        if (TOKEN->type != TK_SEMI)
            NONTERMINAL(ast->return_val, parser_expression(self));
        UPDATECONTEXT(ast->context);
        MATCH(TK_SEMI);
        break;
    }
    return ast;
}

/*
translation_unit:
    external_declaration
    | translation_unit external_declaration
*/
AST *parser_translation_unit(Parser *self)
{
    AST *ast = parser_external_declaration(self);
    AST *p = ast;
    while (p != NULL)
    {
        p->sibling = parser_external_declaration(self);
        p = p->sibling;
        if (p != NULL) p->head_sibling = ast;
    }
    return ast;
}

/*
external_declaration:
    functionn_definition
    | declaration
*/
AST *parser_external_declaration(Parser *self)
{
    STORE(tk);
    AST *ast = NULL;
    if ((ast = parser_functionn_definition(self)) != NULL) return ast;
    LOAD(tk);
    if ((ast = parser_declarator(self)) != NULL) return ast;
    LOAD(tk);
    return ast;
}

/*
functionn_definition:
    | [declaration_specifier] declarator compound_statement
*/
AST *parser_functionn_definition(Parser *self)
{
    STORE(tk);
    NEWCONTEXT(context);
    AST *ast = NULL;
    NEWAST(ast, AT_FUNCTIONDEF, context);
    STORE(tk2);
    ast->funcdef_spec = parser_declaration_specifier(self);
    if (ast->funcdef_spec == NULL) LOAD(tk2);
    NONTERMINAL(ast->funcdef_declor, parser_declarator(self));
    NONTERMINAL(ast->funcdef_body, parser_compound_statement(self));
    UPDATECONTEXT(ast->context);
    return ast;
}

AST *parser_start(Parser *self)
{
    NEWCONTEXT(context);
    AST *ast;
    NEWAST(ast, AT_TRANSLATIONUNIT, context);
    ast->tu_body = parser_translation_unit(self);
    return ast;
}