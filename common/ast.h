#ifndef __AST_H__
#define __AST_H__

#include "type.h"

#ifdef __cplusplus
extern "C" {
#endif

#define MAX_AST_CHILD_NUM 4

#define tu_body child[0]
#define binop_left child[0]
#define binop_right child[1]
#define unaryop_operand child[0]
#define condop_cond child[0]
#define condop_true child[1]
#define condop_false child[2]
#define subscript_target child[0]
#define subscript_index child[1]
#define member_target child[0]
#define call_func child[0]
#define call_args child[1]
#define cast_type child[0]
#define cast_target child[1]
#define decl_spec child[0]
#define decl_declor child[1]
#define initdecl_decl child[0]
#define initdecl_init child[1]
#define recordspec_list child[0]
#define recordspec_decl child[1]
#define recorddeclor_declor child[0]
#define recorddeclor_bit child[1]
#define enum_consts child[0]
#define enumconst_val child[1]
#define initlist_list child[0]
#define declor_sub child[0]
#define arraydeclor_sub declor_sub
#define arraydeclor_len child[1]
#define funcdeclor_sub declor_sub
#define funcdeclor_param child[1]
#define pdeclor_sub child[1]
#define pdeclor_qualifier child[0]
#define typename_specqual child[0]
#define typename_declor child[1]
#define return_val child[0]
#define while_cond child[0]
#define while_body child[1]
#define dowhile_cond child[0]
#define dowhile_body child[1]
#define for_init child[0]
#define for_cond child[1]
#define for_iter child[2]
#define for_body child[3]
#define if_cond child[0]
#define if_body child[1]
#define if_else child[2]
#define switch_expr child[0]
#define switch_body child[1]
#define compound_stmt child[0]
#define label_stmt child[0]
#define case_stmt label_stmt
#define case_expr child[1]
#define default_stmt label_stmt
#define funcdef_param child[0]
#define funcdef_spec child[1]
#define funcdef_declor child[2]
#define funcdef_body child[3]
#define decl_decls child[2]
#define vardecl_init child[0]
#define field_bit child[0]
#define recorddecl_field child[0]

typedef enum { AF_ARROW, AF_POSTFIX, AF_PREFIX, AF_UNION, AF_STRUCT } ASTFlag;

typedef struct {
    char *filename;
    char *line;
    int s_row, s_col; // 起始位置
    int e_row, e_col; // 结束位置
} ASTContext;

typedef enum {
#define ASTKIND(a, b) a,
#include "astkinds.def"
#undef ASTKIND
} ASTKind;

static char *asttype_nams[] = {
#define ASTKIND(a, b) b,
#include "astkinds.def"
#undef ASTKIND
};

typedef struct AST {
    ASTKind kind;
    ASTContext context;
    struct AST *child[MAX_AST_CHILD_NUM]; // 最左子节点
    struct AST *sibling;                  // 右兄弟节点
    struct AST *head_sibling;             // 最左兄弟节点
    char *val;
    int flags;
    Type *type;
} AST;

AST *ast_new();
void ast_init(AST *, ASTKind, ASTContext);
void ast_print(AST *, int indent);
char *ast_tostr(AST *);

#ifdef __cplusplus
}
#endif

#endif