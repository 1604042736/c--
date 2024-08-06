#ifndef __SYMTABLE_H__
#define __SYMTABLE_H__

#include "type.h"

#ifdef __cplusplus
extern "C" {
#endif

#define MAX_ITEM_NUM 1000
#define MAX_TYPE_NUM 1000

typedef struct _ti {
    char *name;
    struct Type *type;
    struct _ti *same_hash;  //把hash值相同的表项串起来
    struct SymTable *table; //所属的符号表
} TableItem;

//每个作用域对应一个符号表
typedef struct SymTable {
    TableItem *items[MAX_ITEM_NUM];
    struct Type *types[MAX_TYPE_NUM];
    int type_num;
} SymTable;

TableItem *tableitem_new();
void tableitem_init(TableItem *, char *name, struct Type *type);

SymTable *symtable_new();
void symtable_init(SymTable *);
void symtable_add(SymTable *, TableItem *);

#ifdef __cplusplus
}
#endif

#endif