#include <stdlib.h>
#include <string.h>

#include "stringutil.h"
#include "symtable.h"
#include "type.h"

TableItem *tableitem_new() { return (TableItem *)malloc(sizeof(TableItem)); }

void tableitem_init(TableItem *self, char *name, struct Type *type)
{
    self->name = name;
    self->type = type;
    self->same_hash =NULL;
    self->table = NULL;
}

SymTable *symtable_new() { return (SymTable *)malloc(sizeof(SymTable)); }

void symtable_init(SymTable *self)
{
    memset(self->items, 0, sizeof(self->items));
    memset(self->types, 0, sizeof(self->types));
    self->type_num = 0;
}

void symtable_add(SymTable *self, TableItem *item)
{
    unsigned long long hash = string_hash(item->name);
    unsigned long long k = hash % MAX_ITEM_NUM;
    if (self->items[k] == NULL)
        self->items[k] = item;
    else //冲突
    {
        TableItem *p = self->items[k];
        while (p->same_hash != NULL) p = p->same_hash;
        p->same_hash = item;
    }
    item->table = self;
}