#ifndef __LEXER_H__
#define __LEXER_H__

#include <stdlib.h>

#include "filecontext.h"
#include "preprocessor.h"
#include "stringutil.h"
#include "token.h"

#ifdef __cplusplus
extern "C" {
#endif

#define PRINT_TOKEN_LIST(h)                                                    \
    do                                                                         \
    {                                                                          \
        Token *_p = h;                                                         \
        while (_p != NULL)                                                     \
        {                                                                      \
            printf("%s ", repr(_p->str));                                      \
            _p = _p->next;                                                     \
        }                                                                      \
        printf("\n");                                                          \
    } while (0)
typedef enum {
    LF_EOF,         //读取到文件末尾
    LF_SKIPSPACE,   //跳过空白字符
    LF_SKIPPP,      //跳过预处理指令
    LF_PPMODE,      //预处理模式
    LF_MERGEROW,    //合并两个物理行
    LF_SKIPCOMMENT, //跳过注释
    LF_CONCAT,      //拼接相邻的字符串常量
} LexerFlag;

typedef struct Line {
    char *buf;
    int pos;
    struct Line *pre, *next;
} Line;

typedef struct {
    FileContext context;
    Token *token;
    Token *token_head;
    char ch;
    int flag;
    Line *line;
    Preprocessor *pp;
} Lexer;

Lexer *lexer_new();
void lexer_init(Lexer *, FILE *, char *filename);
void lexer_getch(Lexer *);
void lexer_ungetch(Lexer *);
char lexer_get_escape(Lexer *, char c);
void lexer_gettoken(Lexer *);
void lexer_ungettoken(Lexer *);
void lexer_handle_directive(Lexer *);
void lexer_expand_macro(Lexer *);
MacroArg *lexer_get_macro_args(Lexer *, Macro *macro, int *arg_num);
void lexer_include(Lexer *, char *filename, int include_std);

#ifdef __cplusplus
}
#endif

#endif