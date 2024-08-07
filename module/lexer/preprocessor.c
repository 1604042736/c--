#include <stdlib.h>
#include <string.h>

#include "preprocessor.h"

Macro *macro_new() { return (Macro *)malloc(sizeof(Macro)); }

void macro_init(Macro *self, char *name, Token *parameters, Token *body)
{
    self->name = name;
    self->parameters = parameters;
    self->body = body;
    self->pre = NULL;
    self->next = NULL;
}

Token *macroarg_find(MacroArg *self, char *name, int arg_num)
{
    for (int i = 0; i < arg_num; i++)
    {
        if (!strcmp(self[i].param, name)) return self[i].arg;
    }
    return NULL;
}

Preprocessor *preprocessor_new()
{
    return (Preprocessor *)malloc(sizeof(Preprocessor));
}

void preprocessor_init(Preprocessor *self)
{
    self->macros = NULL;
    self->ip_len = 0;
    self->include_paths[self->ip_len++] = ".";
    self->cr_pos = -1;
    self->cp_pos = -1;
}

Macro *preprocessor_find_macro(Preprocessor *self, char *name)
{
    Macro *m = self->macros;
    while (m != NULL)
    {
        if (!strcmp(name, m->name)) return m;
        m = m->next;
    }
    return NULL;
}

void preprocessor_add_macro(Preprocessor *self, Macro *macro)
{
    if (self->macros == NULL)
    {
        self->macros = macro;
        return;
    }
    Macro *p = self->macros;
    while (p->next != NULL) p = p->next;
    p->next = macro;
    macro->pre = p;
}