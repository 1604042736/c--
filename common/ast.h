#ifndef __AST_H__
#define __AST_H__

#ifdef __cplusplus
extern "C"
{
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
#define souspec_list child[0]
#define structdeclor_declor child[0]
#define structdeclor_const child[1]
#define enum_enumor child[0]
#define enumor_const child[1]
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
#define funcdef_spec child[0]
#define funcdef_declor child[1]
#define funcdef_body child[2]

#define FLAG_ARROW 1
#define FLAG_POSTFIX 1 << 2
#define FLAG_PREFIX 1 << 3

    typedef struct
    {
        char *filename;
        char *line;
        int s_row, s_col; // 起始位置
        int e_row, e_col; // 结束位置
    } ASTContext;

    typedef enum
    {
#define ASTTYPE(a, b) a,
#include "asttypes.def"
#undef ASTTYPE
    } ASTType;

    static char *asttype_nams[] = {
#define ASTTYPE(a, b) b,
#include "asttypes.def"
#undef ASTTYPE
    };

    typedef struct AST
    {
        ASTType type;
        ASTContext context;
        struct AST *child[MAX_AST_CHILD_NUM]; // 最左子节点
        struct AST *sibling;                  // 右兄弟节点
        struct AST *head_sibling;             // 最左兄弟节点
        char *val;
        int flags;
    } AST;

    AST *ast_new();
    void ast_init(AST *, ASTType, ASTContext);
    void ast_print(AST *, int indent);

#ifdef __cplusplus
}
#endif

#endif