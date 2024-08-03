#ifndef __LEXER_H__
#define __LEXER_H__

#include "token.h"
#include "filecontext.h"
#include "preprocessor.h"

#ifdef __cplusplus
extern "C"
{
#endif

    typedef struct Line
    {
#define BUF_SIZE 1000
        char buf[BUF_SIZE];
        int pos;
        struct Line *pre, *next;
    } Line;

    typedef struct
    {
        FileContext context;
        char ch;
        Token *token;
        Token *token_head; // 头指针
        Line *lines;
        Preprocessor *pp; // 预处理器
        int eof;
        int ignore_pp;    // 忽略预处理器指令
        int ignore_space; // 忽略空白字符
        int merge_row;    // 合并两行
    } Lexer;

    Lexer *lexer_new();
    void lexer_init(Lexer *, FILE *, char *filename);
    void lexer_getch(Lexer *);
    void lexer_ungetch(Lexer *);
    void lexer_gettoken(Lexer *);
    void lexer_ungettoken(Lexer *);
    void lexer_match(Lexer *, TokenType actual, TokenType expected, char *, ...);
    void lexer_handle_directive(Lexer *);
    void lexer_expand_macro(Lexer *);
    MacroArg *lexer_get_macro_args(Lexer *, Macro *, int *arg_num);
    void lexer_include(Lexer *, char *filename, int include_std);

#ifdef __cplusplus
}
#endif

#endif