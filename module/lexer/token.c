#include <stdlib.h>
#include <string.h>

#include "token.h"

Token *token_new()
{
    return (Token *)malloc(sizeof(Token));
}

void token_init(Token *self, TokenType type, FileContext filecontext, char *str)
{
    self->type = type;
    self->context = filecontext;
    self->str = str;
    self->pre = NULL;
    self->next = NULL;
}

Token *token_copy(Token *self)
{
    Token *tk = token_new();
    memcpy(tk, self, sizeof(Token));
    return tk;
}