#ifndef __TOKEN_H__
#define __TOKEN_H__

#include "filecontext.h"

#define IS_SPACE_TOKEN(tk) (tk->type == TK_UNKNOWN && isspace(tk->str[0]))
#define CONNECT(start, end)                                                    \
    do                                                                         \
    {                                                                          \
        if ((start) != NULL && (end) != NULL)                                  \
        {                                                                      \
            (start)->next = end;                                               \
            (end)->pre = start;                                                \
        }                                                                      \
    } while (0)

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
#define TK(a, b) a,
#define COMMON TK
#define KEYWORD TK
#define SPECIAL(a) a,
#include "tokentypes.def"
#undef KEYWORD
#undef COMMON
#undef TK
#undef SPECIAL
} TokenType;

static struct {
    TokenType type;
    char *name;
} keyword_type_names[] = {
#define COMMON(a, b)
#define SPECIAL(a)
#define KEYWORD(a, b) {a, b},
#include "tokentypes.def"
#undef KEYWORD
#undef COMMON
#undef SPECIAL
};
static int KEYWORD_NUM =
    sizeof(keyword_type_names) / sizeof(keyword_type_names[0]);

static char *token_names[] = {
#define TK(a, b) #a,
#define COMMON(a, b) TK(a, b)
#define KEYWORD(a, b) TK(a, b)
#define SPECIAL(a) #a,
#include "tokentypes.def"
#undef KEYWORD
#undef COMMON
#undef TK
#undef SPECIAL
};
static int TOKEN_NUM = sizeof(token_names) / sizeof(token_names[0]);

typedef struct Token {
    TokenType type;
    FileContext context;
    char *str;

    struct Token *pre, *next;
} Token;

Token *token_new();
void token_init(Token *, TokenType, FileContext, char *);
Token *token_copy(Token *);

#ifdef __cplusplus
}
#endif

#endif