/*
分析语法树中的声明, 并调整语法树结构
这个阶段产生的用户自定义的类型都是不完整的, 不能直接拿来使用
*/

#ifndef __DECLANALYZER_H__
#define __DECLANALYZER_H__

#include "ast.h"
#include "symtable.h"
#include "type.h"

#ifdef __cplusplus
extern "C" {
#endif

#define MAX_SYMTAB_NUM 100
#define MAX_PARAM_NUM 100

typedef struct {
    Type *type; //当前分析到的类型
    int flag;   // 用于保存未分析到类型时已经遇到的flag
    char *name; //分析时遇到的Name
    char *param_names[MAX_PARAM_NUM];        //保存参数名
    ASTContext param_context[MAX_PARAM_NUM]; //保存参数所在的上下文
    int param_num;
} DeclAnalyzer;

DeclAnalyzer *declanalyzer_new();
void declanalyzer_init(DeclAnalyzer *);
void declanalyzer_analyze(DeclAnalyzer *, AST *);

#ifdef __cplusplus
}
#endif

#endif