#include <stdlib.h>
#include <string.h>

#include "ast.h"
#include "stringutil.h"
#include "type.h"


ParamAttribute *paramattr_new()
{
    return (ParamAttribute *)malloc(sizeof(ParamAttribute));
}

void paramattr_init(ParamAttribute *self, Type *type, Type *function)
{
    self->type = type;
    self->function = function;
    self->pre = self->next = NULL;
}

Type *type_new() { return (Type *)malloc(sizeof(Type)); }

void type_init(Type *self, TypeKind kind)
{
    memset(self, 0, sizeof(Type));
    self->kind = kind;
}

char *type_tostr(Type *self)
{
    char *s = empty_string();
    switch (self->kind)
    {
    case T_VOID:
    case T_CHAR:
    case T_INT:
    case T_LONG:
    case T_LONGLONG:
        if (CHECK_FLAG(self->flag, TF_UNSIGNED)) s = add_string(s, "unsigned ");
    case T_FLOAT:
    case T_DOUBLE: s = add_string(s, type_names[self->kind]); break;
    case T_POINTER:
        s = add_string(s, type_tostr(self->t.pointee_type));
        s = add_char(s, '*');
        break;
    case T_ARRAY:
        s = add_string(s, type_tostr(self->t.array.element_type));
        s = add_char(s, '[');
        if (self->t.array.size != NULL)
            s = add_string(s, ast_tostr(self->t.array.size));
        s = add_char(s, ']');
        break;
    case T_FUNCTION:
        s = add_string(s, type_tostr(self->t.function.return_type));
        s = add_char(s, '(');
        if (self->t.function.param_types)
        {
            ParamAttribute *t = self->t.function.param_types;
            while (t != NULL)
            {
                s = add_string(s, type_tostr(t->type));
                if (t->next != NULL) s = add_char(s, ',');
                t = t->next;
            }
        }
        if (self->t.function.has_varparm)
        {
            if (self->t.function.param_types) s = add_char(s, ',');
            s = add_string(s, "...");
        }
        s = add_char(s, ')');
        break;
    case T_ENUM:
    case T_UNION:
    case T_STRUCT:
        if (self->kind == T_ENUM)
            s = add_string(s, "enum ");
        else if (self->kind == T_UNION)
            s = add_string(s, "union ");
        else if (self->kind == T_STRUCT)
            s = add_string(s, "struct ");
        if (self->name != NULL)
            s = add_string(s, self->name);
        else
            s = add_string(s, "<unnamed>");
        break;
    case T_TYPEDEF:
        s = add_string(s, self->name);
        s = add_char(s, ':');
        if (self->t.typedef_type != NULL)
            s = add_string(s, type_tostr(self->t.typedef_type));
        break;
    }
    return s;
}