#ifndef __TYPE_H__
#define __TYPE_H__

#include "symtable.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    TF_UNSIGNED,
    TF_TYPEDEF, //专用于declanalyzer
    TF_EXTERN,
    TF_STATIC,
    TF_AUTO,
    TF_REGISTER,
    TF_CONST,
    TF_VOLATILE
} TypeFlag;

#define CHECK_FLAG(flag, f) ((flag >> f) & 1 == 1)
#define ADD_FLAG(flag, f) flag = flag | (1 << f)
#define REMOVE_FLAG(flag, f) flag = flag & ~(1 << f)

typedef enum {
#define BUILTINTYPE(a, b) a,
#define DERIVEDTYPE(a) a,
#define TYPEKIND(a) a,
#include "types.def"
#undef BUILTINTYPE
#undef DERIVEDTYPE
#undef TYPEKIND
} TypeKind;

static char *type_names[] = {
#define BUILTINTYPE(a, b) b,
#define DERIVEDTYPE(a)
#define TYPEKIND(a)
#include "types.def"
#undef BUILTINTYPE
#undef DERIVEDTYPE
#undef TYPEKIND
};

typedef struct _pa {
    struct Type *type;
    struct Type *function;
    struct _pa *pre, *next;
} ParamAttribute;

typedef struct _ea {
    char *name;
    int val;
    struct Type *enum_type;
    struct _ea *pre, *next;
} EnumAttribute;

typedef struct Type {
    TypeKind kind;
    int flag;
    char *name;
    union {
        struct Type *pointee_type;
        struct {
            struct Type *element_type;
            struct AST *size;
        } array;
        struct {
            struct Type *return_type;
            ParamAttribute *param_types;
            int has_varparm; //变长参数
        } function;
        struct SymTable *fields;
        EnumAttribute *constants;
        struct Type *typedef_type;
    } t;
} Type;

ParamAttribute *paramattr_new();
void paramattr_init(ParamAttribute *, Type *type, Type *function);

Type *type_new();
void type_init(Type *, TypeKind);
char *type_tostr(Type *);

#ifdef __cplusplus
}
#endif

#endif