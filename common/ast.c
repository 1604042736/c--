#include <stdlib.h>
#include <stdio.h>

#include "ast.h"

AST *ast_new()
{
    return (AST *)malloc(sizeof(AST));
}

void ast_init(AST *self, ASTType type, ASTContext context)
{
    self->type = type;
    self->context = context;
    for (int i = 0; i < MAX_AST_CHILD_NUM; i++)
        self->child[i] = NULL;
    self->sibling = NULL;
    self->head_sibling = self;
    self->val = "\0";
    self->flags = 0;
}

void ast_print(AST *self, int indent)
{
    AST *p = self;
    while (p != NULL)
    {
        for (int i = 0; i < indent; i++)
            printf("  ");
        printf("%s ", asttype_nams[p->type]);
        printf("<%s:(%d:%d):(%d:%d)> ",
               p->context.filename,
               p->context.s_row, p->context.s_col,
               p->context.e_row, p->context.e_col);
        printf("%s", p->val);
        printf("\n");
        for (int i = 0; i < MAX_AST_CHILD_NUM; i++)
            ast_print(p->child[i], indent + 1);
        p = p->sibling;
    }
}