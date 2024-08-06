#include <stdio.h>
#include <stdlib.h>

#include "ast.h"
#include "stringutil.h"

AST *ast_new() { return (AST *)malloc(sizeof(AST)); }

void ast_init(AST *self, ASTKind kind, ASTContext context)
{
    self->kind = kind;
    self->context = context;
    for (int i = 0; i < MAX_AST_CHILD_NUM; i++) self->child[i] = NULL;
    self->sibling = NULL;
    self->head_sibling = self;
    self->val = "\0";
    self->flag = 0;
    self->type = NULL;
}

void ast_print(AST *self, int indent)
{
    AST *p = self;
    while (p != NULL)
    {
        for (int i = 0; i < indent; i++) printf("  ");
        printf("%s ", asttype_nams[p->kind]);
        printf("<%s:(%d:%d):(%d:%d)> ", p->context.filename, p->context.s_row,
               p->context.s_col, p->context.e_row, p->context.e_col);
        switch (p->kind)
        {
        case AK_CHAR:
        case AK_STRING: printf("%s ", repr(p->val)); break;
        default: printf("%s ", p->val);
        }
        if (p->type != NULL) printf("%s ", type_tostr(p->type));
        switch (p->kind)
        {
        case AK_RECORDDECL:
        case AK_RECORDSPECIFIER:
            if (CHECK_FLAG(p->flag, AF_STRUCT))
                printf("struct ");
            else
                printf("union ");
            break;
        }
        printf("\n");
        for (int i = 0; i < MAX_AST_CHILD_NUM; i++)
            ast_print(p->child[i], indent + 1);
        p = p->sibling;
    }
}

char *ast_tostr(AST *self)
{
    char *s = empty_string();
    switch (self->kind)
    {
    case AK_NAME:
    case AK_INTEGER:
    case AK_STRING:
    case AK_FLOAT:
    case AK_CHAR: s = add_string(s, self->val); break;
    case AK_UNARYOPERATOR:
        s = add_string(s, self->val);
        s = add_string(s, ast_tostr(self->unaryop_operand));
        break;
    case AK_BINARYOPERATOR:
        s = add_string(s, ast_tostr(self->binop_left));
        s = add_string(s, self->val);
        s = add_string(s, ast_tostr(self->binop_right));
        break;
    case AK_CONDITIONALOPERATOR:
        s = add_string(s, ast_tostr(self->condop_cond));
        s = add_char(s, '?');
        s = add_string(s, ast_tostr(self->condop_true));
        s = add_char(s, ':');
        s = add_string(s, ast_tostr(self->condop_false));
        break;
    case AK_SUBSCRIPT:
        s = add_string(s, ast_tostr(self->subscript_target));
        s = add_char(s, '[');
        s = add_string(s, ast_tostr(self->subscript_index));
        s = add_char(s, ']');
        break;
    case AK_MEMBER:
        s = add_string(s, ast_tostr(self->member_target));
        if (CHECK_FLAG(self->flag, AF_ARROW))
            s = add_string(s, "->");
        else
            s = add_char(s, '.');
        s = add_string(s, self->val);
        break;
    }
    return s;
}