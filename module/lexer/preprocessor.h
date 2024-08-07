#ifndef __PREPROCESSOR_H__
#define __PREPROCESSOR_H__

#include "token.h"

#define MAX_INCLUDE_PATH_NUM 100
#define MAX_CONDITION_LEVEL 100

#ifdef __cplusplus
extern "C" {
#endif

typedef struct Macro {
    char *name;
    Token *parameters;
    Token *body;

    struct Macro *pre, *next;
} Macro;

typedef struct {
    char *param; // 参数名
    Token *arg;
    int is_va_arg; // 是否是变长参数
} MacroArg;

typedef struct {
    char *include_paths[MAX_INCLUDE_PATH_NUM];
    int ip_len;
    Macro *macros;
    int condi_result[MAX_CONDITION_LEVEL]; // 条件包含指令的每一层结果
    int cr_pos;
    Token *condi_pre[MAX_CONDITION_LEVEL]; // 每个条件包含指令的前一个token
    int cp_pos;
} Preprocessor;

Macro *macro_new();
void macro_init(Macro *macro, char *name, Token *parameters, Token *body);

Token *macroarg_find(MacroArg *, char *name, int arg_num);

Preprocessor *preprocessor_new();
void preprocessor_init(Preprocessor *);
Macro *preprocessor_find_macro(Preprocessor *, char *name);
void preprocessor_add_macro(Preprocessor *, Macro *);

#ifdef __cplusplus
}
#endif

#endif