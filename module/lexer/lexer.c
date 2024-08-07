#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "assert.h"
#include "ast.h"
#include "error.h"
#include "lexer.h"
#include "stringutil.h"
#include "warning.h"

Lexer *lexer_new() { return (Lexer *)malloc(sizeof(Lexer)); }

void lexer_init(Lexer *self, FILE *file, char *filename)
{
    filecontext_init(&self->context, file, filename, 1, 0);
    self->token = self->token_head = NULL;
    self->flag = 0;
    self->line = NULL;
    self->pp = preprocessor_new();
    preprocessor_init(self->pp);
    ADD_FLAG(self->flag, LF_SKIPSPACE);
    ADD_FLAG(self->flag, LF_SKIPCOMMENT);
    ADD_FLAG(self->flag, LF_CONCAT);
}

#define NEW_LINE (Line *)malloc(sizeof(Line))

void lexer_init_line(Lexer *self, Line *line)
{
    line->pos = 0;
    line->pre = line->next = NULL;
    line->buf = empty_string();
    char c;
    do
    {
        c = fgetc(self->context.file);
        line->buf = add_char(line->buf, c);
    } while (c != '\n' && c != EOF);
}

void lexer_getch(Lexer *self)
{
    if (self->line == NULL)
    {
        self->line = NEW_LINE;
        lexer_init_line(self, self->line);
    }
    if (self->line->pos >= strlen(self->line->buf))
    {
        if (CHECK_FLAG(self->flag, LF_EOF))
        {
            self->ch = EOF;
            return;
        }
        if (self->line->next == NULL)
        {
            Line *new_line = NEW_LINE;
            lexer_init_line(self, new_line);
            self->line->next = new_line;
            new_line->pre = self->line;
        }
        self->line = self->line->next;
        self->context.row++;
        self->context.col = 0;
        if (CHECK_FLAG(self->flag, LF_MERGEROW))
            REMOVE_FLAG(self->flag, LF_MERGEROW);
        else
            self->context.l_row++;
    }
    self->context.col++;
    self->ch = self->line->buf[self->line->pos++];
    if (self->ch == EOF)
        ADD_FLAG(self->flag, LF_EOF);
    else if (self->ch == '\\')
    {
        if (self->line->pos >= strlen(self->line->buf)
            || self->line->buf[self->line->pos] == '\n')
        {
            ADD_FLAG(self->flag, LF_MERGEROW);
            self->line->pos = strlen(self->line->buf); //强制结束这一行
            lexer_getch(self);
        }
    }
}

void lexer_ungetch(Lexer *self)
{
    if (self->line->pos <= 0) //回到上一行
    {
        self->line = self->line->pre;
        self->line->pos = strlen(self->line->buf) - 1;
        self->context.row--;
        self->context.l_row--;
        self->context.col = self->line->pos;
    }
    else
    {
        self->line->pos--;
        self->context.col--;
    }
}

char lexer_get_escape(Lexer *self, char c)
{
    switch (c)
    {
    case '\'': return '\'';
    case '"': return '"';
    case '\\': return '\\';
    case 'a': return '\a';
    case 'b': return '\b';
    case 'f': return '\f';
    case 'n': return '\n';
    case 'r': return '\r';
    case 't': return '\t';
    case 'v': return '\v';
    case '0': return '\0';
    default:
        warning(self->context, "unknown escape sequence '\\%c'\n", c);
        return c;
    }
}

void lexer_gettoken(Lexer *self)
{
#define TOKEN(t, s) token_init(self->token, t, context, s)
start:
    Token *pre = NULL;
    if (self->token != NULL) pre = self->token->pre;
    if (self->token != NULL && self->token->next != NULL)
    {
        pre = self->token;
        self->token = self->token->next;
        goto token_got;
    }
    pre = self->token;
    self->token = token_new();
    lexer_getch(self);
    FileContext context = self->context;
    switch (self->ch)
    {
    case EOF: TOKEN(TK_END, "<eof>"); goto token_got;
    case '[': TOKEN(TK_LSQUARE, "["); goto token_got;
    case ']': TOKEN(TK_RSQUARE, "]"); goto token_got;
    case '(': TOKEN(TK_LPAREN, "("); goto token_got;
    case ')': TOKEN(TK_RPAREN, ")"); goto token_got;
    case '{': TOKEN(TK_LBRACE, "{"); goto token_got;
    case '}': TOKEN(TK_RBRACE, "}"); goto token_got;
    case '.': {
        lexer_getch(self);
        if (self->ch == '.')
        {
            lexer_getch(self);
            if (self->ch == '.')
                TOKEN(TK_ELLIPSIS, "...");
            else
            {
                lexer_ungetch(self);
                lexer_ungetch(self);
            }
        }
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_PERIOD, ".");
        }
        goto token_got;
    }
    case '&': {
        lexer_getch(self);
        if (self->ch == '&')
            TOKEN(TK_AMPAMP, "&&");
        else if (self->ch == '=')
            TOKEN(TK_AMPEQUAL, "&=");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_AMP, "&");
        }
        goto token_got;
    }
    case '*': {
        lexer_getch(self);
        if (self->ch == '=')
            TOKEN(TK_STAREQUAL, "*=");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_STAR, "*");
        }
        goto token_got;
    }
    case '+': {
        lexer_getch(self);
        if (self->ch == '+')
            TOKEN(TK_PLUSPLUS, "++");
        else if (self->ch == '=')
            TOKEN(TK_PLUSEQUAL, "+=");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_PLUS, "+");
        }
        goto token_got;
    }
    case '-': {
        lexer_getch(self);
        if (self->ch == '-')
            TOKEN(TK_MINUSMINUS, "--");
        else if (self->ch == '=')
            TOKEN(TK_MINUSEQUAL, "-=");
        else if (self->ch == '>')
            TOKEN(TK_ARROW, "->");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_MINUS, "-");
        }
        goto token_got;
    }
    case '~': TOKEN(TK_TILDE, "~"); goto token_got;
    case '!': {
        lexer_getch(self);
        if (self->ch == '=')
            TOKEN(TK_EXCLAIMEQUAL, "!=");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_EXCLAIM, "!");
        }
        goto token_got;
    }
    case '/': {
        lexer_getch(self);
        if (self->ch == '=')
            TOKEN(TK_SLASHEQUAL, "/=");
        else if (self->ch == '/')
        {
            char *str = empty_string();
            lexer_getch(self);
            while (self->ch != '\n')
            {
                str = add_char(str, self->ch);
                lexer_getch(self);
            }
            if (CHECK_FLAG(self->flag, LF_SKIPCOMMENT))
            {
                free(self->token);
                self->token = pre;
                lexer_gettoken(self);
                return;
            }
            TOKEN(TK_COMMENT, str);
        }
        else if (self->ch == '*')
        {
            char *str = empty_string();
            lexer_getch(self);
            while (self->ch != EOF)
            {
                if (self->ch == '*')
                {
                    lexer_getch(self);
                    if (self->ch == '/')
                        break;
                    else
                    {
                        str = add_char(str, '*');
                        str = add_char(str, self->ch);
                    }
                }
                else
                    str = add_char(str, self->ch);
                lexer_getch(self);
            }
            if (self->ch == EOF)
                warning(self->context, "unterminated /* comment");
            if (CHECK_FLAG(self->flag, LF_SKIPCOMMENT))
            {
                free(self->token);
                self->token = pre;
                lexer_gettoken(self);
                return;
            }
            TOKEN(TK_COMMENT, str);
        }
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_SLASH, "/");
        }
        goto token_got;
    }
    case '%': {
        lexer_getch(self);
        if (self->ch == '=')
            TOKEN(TK_PERCENTEQUAL, "%=");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_PERCENT, "%");
        }
        goto token_got;
    }
    case '<': {
        if (!CHECK_FLAG(self->flag, LF_PPMODE))
        {
            lexer_getch(self);
            if (self->ch == '<')
            {
                lexer_getch(self);
                if (self->ch == '=')
                    TOKEN(TK_LESSLESSEQUAL, "<<=");
                else
                {
                    lexer_ungetch(self);
                    TOKEN(TK_LESSLESS, "<<");
                }
            }
            else if (self->ch == '=')
                TOKEN(TK_LESSEQUAL, "<=");
            else
            {
                lexer_ungetch(self);
                TOKEN(TK_LESS, "<");
            }
        }
        else
        {
            char *str = empty_string();
            lexer_getch(self);
            do
            {
                str = add_char(str, self->ch);
                lexer_getch(self);
            } while (self->ch != '>');
            TOKEN(TK_HEADERNAME, str);
        }
        goto token_got;
    }
    case '>': {
        lexer_getch(self);
        if (self->ch == '>')
        {
            lexer_getch(self);
            if (self->ch == '=')
                TOKEN(TK_GREATERGREATEREQUAL, ">>=");
            else
            {
                lexer_ungetch(self);
                TOKEN(TK_GREATERGREATER, ">>");
            }
        }
        else if (self->ch == '=')
            TOKEN(TK_GREATEREQUAL, ">=");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_GREATER, ">");
        }
        goto token_got;
    }
    case '^': {
        lexer_getch(self);
        if (self->ch == '=')
            TOKEN(TK_CARETEQUAL, "^=");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_CARET, "^");
        }
        goto token_got;
    }
    case '|': {
        lexer_getch(self);
        if (self->ch == '=')
            TOKEN(TK_PIPEEQUAL, "|=");
        else if (self->ch == '|')
            TOKEN(TK_PIPEPIPE, "||");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_PIPE, "|");
        }
        goto token_got;
    }
    case '?': TOKEN(TK_QUESTION, "?"); goto token_got;
    case ':': TOKEN(TK_COLON, ":"); goto token_got;
    case ';': TOKEN(TK_SEMI, ";"); goto token_got;
    case '=': {
        lexer_getch(self);
        if (self->ch == '=')
            TOKEN(TK_EQUALEQUAL, "==");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_EQUAL, "=");
        }
        goto token_got;
    }
    case ',': TOKEN(TK_COMMA, ","); goto token_got;
    case '\'': {
        char *str = (char *)malloc(sizeof(char) * 2);
        lexer_getch(self);
        if (self->ch == '\\')
        {
            lexer_getch(self);
            str[0] = lexer_get_escape(self, self->ch);
        }
        else
            str[0] = self->ch;
        str[1] = '\0';
        lexer_getch(self);
        if (self->ch != '\'')
        {
            lexer_ungetch(self);
            warning(self->context, "missing terminating ' character");
        }
        TOKEN(TK_CHARCONST, str);
        goto token_got;
    }
    case '"': {
        char *str = empty_string();
        lexer_getch(self);
        while (self->ch != '"' && self->ch != EOF)
        {
            if (self->ch == '\\')
            {
                lexer_getch(self);
                str = add_char(str, lexer_get_escape(self, self->ch));
            }
            else
                str = add_char(str, self->ch);
            lexer_getch(self);
        }
        if (self->ch == EOF)
            warning(self->context, "missing terminating '\"' character");
        TOKEN(TK_STRINGCONST, str);
        goto token_got;
    }
    case '#': {
        lexer_getch(self);
        if (self->ch == '#')
            TOKEN(TK_HASHHASH, "##");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_HASH, "#");
        }
        goto token_got;
    }
    case '\n':
        if (CHECK_FLAG(self->flag, LF_SKIPSPACE)
            && !CHECK_FLAG(self->flag, LF_PPMODE))
            goto white_space;
        TOKEN(TK_NEWLINE, "\n");
        goto token_got;
    }

    if (isalpha(self->ch) || self->ch == '_')
    {
        char *str = empty_string();
        do
        {
            str = add_char(str, self->ch);
            lexer_getch(self);
        } while (isalpha(self->ch) || isdigit(self->ch) || self->ch == '_');
        TokenType type = TK_NAME;
        for (int i = 0; i < KEYWORD_NUM; i++)
        {
            if (!strcmp(keyword_type_names[i].name, str))
            {
                type = keyword_type_names[i].type;
                break;
            }
        }
        TOKEN(type, str);
        lexer_ungetch(self);
    }
    else if (isdigit(self->ch))
    {
        char *str = empty_string();
        do
        {
            str = add_char(str, self->ch);
            lexer_getch(self);
        } while (isdigit(self->ch));
        TokenType type = TK_INTCONST;
        if (self->ch == '.')
        {
            type = TK_FLOATCONST;
            do
            {
                str = add_char(str, self->ch);
                lexer_getch(self);
            } while (isdigit(self->ch));
        }
        lexer_ungetch(self);
        TOKEN(type, str);
    }
    else if (isspace(self->ch))
    {
    white_space:
        char *str = empty_string();
        do
        {
            str = add_char(str, self->ch);
            lexer_getch(self);
        } while (isspace(self->ch) && self->ch != EOF);
        lexer_ungetch(self);
        if (CHECK_FLAG(self->flag, LF_SKIPSPACE))
        {
            free(str);
            free(self->token);
            self->token = pre;
            lexer_gettoken(self);
            return;
        }
        TOKEN(TK_SPACE, str);
    }
    else
    {
        char *str = (char *)malloc(2);
        str[0] = self->ch;
        str[1] = '\0';
        TOKEN(TK_UNKNOWN, str);
    }

token_got:

    self->token->pre = pre;
    if (pre != NULL) pre->next = self->token;
    if (self->token_head == NULL) self->token_head = self->token;
    int _pp_pos = self->pp->cp_pos; //保存
    if (!CHECK_FLAG(self->flag, LF_SKIPPP))
    {
        while (self->token->type == TK_HASH) lexer_handle_directive(self);
        Token *tk = self->token;
        while (self->token->type == TK_NAME)
        {
            lexer_expand_macro(self);
            if (tk->type == self->token->type
                && !strcmp(tk->str, self->token->str))
                break; //相当于没有进行替换
            tk = self->token;
        }
    }
    //在这里token链表中不会删除这个TK_SPACE
    if (CHECK_FLAG(self->flag, LF_SKIPSPACE)
        && (self->token->type == TK_SPACE
            || !CHECK_FLAG(self->flag, LF_PPMODE)
                   && self->token->type == TK_NEWLINE))
    {
        lexer_gettoken(self);
        return;
    }
    if (CHECK_FLAG(self->flag, LF_CONCAT)
        && self->token->type == TK_STRINGCONST) //拼接相邻的字符串字面量
    {
        pre = self->token;
        lexer_gettoken(self);
        if (self->token->type == TK_STRINGCONST)
        {
            char *str = empty_string(self);
            str = add_string(str, pre->str);
            str = add_string(str, self->token->str);
            pre->str = str;

            pre->next = self->token->next;
            if (self->token->next != NULL) self->token->next->pre = pre;

            self->token = pre;
        }
        else
            lexer_ungettoken(self);
    }
    if (self->pp->cr_pos != -1
        && !CHECK_FLAG(self->flag, LF_PPMODE)) //说明正在进行条件预处理
    {
        if (self->pp->cr_pos
            != _pp_pos) //说明这是条件预处理指令之后遇到的第一个token
        {
            Token *tk = self->token->pre;
            lexer_gettoken(self);
            self->token = tk->next;
        }
        else
            goto start;
    }
}

void lexer_ungettoken(Lexer *self)
{
    if (self->token != NULL) self->token = self->token->pre;
}

#define SAVE_FLAG int _flag = self->flag
#define RESTORE_FLAG self->flag = _flag
#define FOLLOWINGTOKEN                                                         \
    do                                                                         \
    {                                                                          \
        SAVE_FLAG;                                                             \
        ADD_FLAG(self->flag, LF_SKIPPP);                                       \
        lexer_gettoken(self);                                                  \
        RESTORE_FLAG;                                                          \
        tail = self->token;                                                    \
    } while (self->token->type == TK_NEWLINE)

#define CONNECT_HEAD(head, end)                                                \
    do                                                                         \
    {                                                                          \
        if (head != NULL)                                                      \
            CONNECT(head, end);                                                \
        else                                                                   \
            self->token_head = end;                                            \
    } while (0)

void lexer_handle_directive(Lexer *self)
{
    assert(self->token->type == TK_HASH);
    Token *head = self->token->pre;
    Token *tail = NULL;
    SAVE_FLAG;
    ADD_FLAG(self->flag, LF_PPMODE);
    lexer_gettoken(self);
    if (!strcmp(self->token->str, "define"))
    {
        lexer_gettoken(self);
        char *name = self->token->str;
        if (self->token->type != TK_NAME)
            error(self->token->context, "macro name must be an identifier");
        Token *parameters = NULL;
        lexer_getch(self);
        if (self->ch == '(')
        {
            SAVE_FLAG;
            ADD_FLAG(self->flag, LF_PPMODE);
            lexer_gettoken(self);
            Token *p = NULL;
            while (self->token->type != TK_RPAREN && self->token->type != TK_END
                   && self->token->type != TK_NEWLINE)
            {
                if (self->token->type != TK_NAME
                    && self->token->type != TK_ELLIPSIS)
                    error(self->context,
                          "invalid token in macro parameter list");
                if (p == NULL)
                    parameters = p = token_copy(self->token);
                else
                {
                    p->next = token_copy(self->token);
                    p->next->pre = p;
                    p = p->next;
                }
                p->next = NULL;
                lexer_gettoken(self);
                if (!(self->token->type != TK_RPAREN
                      && self->token->type != TK_END
                      && self->token->type != TK_NEWLINE))
                    break;
                if (self->token->type != TK_COMMA)
                    error(self->context,
                          "expected a ',' between two parameters");
                lexer_gettoken(self);
            }
            if (self->token->type != TK_RPAREN)
                error(self->context, "missing ')' in parameter list");
            RESTORE_FLAG;
        }
        else
            lexer_ungetch(self);
        Token *body = NULL;
        Token *p = NULL;

        SAVE_FLAG;
        ADD_FLAG(self->flag, LF_PPMODE);
        ADD_FLAG(self->flag, LF_SKIPPP);
        REMOVE_FLAG(self->flag, LF_SKIPSPACE);
        lexer_gettoken(self);
        while (self->token->type != TK_NEWLINE)
        {
            if (p == NULL)
                body = p = token_copy(self->token);
            else
            {
                p->next = token_copy(self->token);
                p->next->pre = p;
                p = p->next;
            }
            p->next = NULL;
            lexer_gettoken(self);
        }
        if (p->type == TK_SPACE) p->pre->next = NULL;
        if (body->type == TK_SPACE) body = body->next;
        p = body;
        while (p != NULL)
        {
            if (p->type == TK_SPACE) p->str = " ";
            p = p->next;
        }
        RESTORE_FLAG;

        Macro *macro = macro_new();
        macro_init(macro, name, parameters, body);
        preprocessor_add_macro(self->pp, macro);

        FOLLOWINGTOKEN;
    }
    else if (!strcmp(self->token->str, "undef"))
    {
        lexer_gettoken(self);
        if (self->token->type != TK_NAME)
            error(self->context, "macro name must be an identitifer");
        Macro *p = self->pp->macros;
        while (p != NULL)
        {
            if (!strcmp(p->name, self->token->str))
            {
                if (p->next != NULL) p->next->pre = p->pre;
                if (p->pre != NULL)
                    p->pre->next = p->next;
                else
                    self->pp->macros = p->next;
                break;
            }
            p = p->next;
        }
        FOLLOWINGTOKEN;
    }
    else if (!strcmp(self->token->str, "include"))
    {
        lexer_gettoken(self);
        char *filename;
        int include_std;
        if (self->token->type == TK_STRINGCONST)
        {
            include_std = 0;
            filename = self->token->str;
        }
        else if (self->token->type == TK_HEADERNAME)
        {
            include_std = 1;
            filename = self->token->str;
        }
        else
            error(self->context, "expected \"FILENAME\" or <FILENAME>");
        lexer_include(self, filename, include_std);
    }
    else if (!strcmp(self->token->str, "if"))
    {
        error(self->context, "incomplete");
    }
    else if (!strcmp(self->token->str, "ifdef")
             || !strcmp(self->token->str, "ifndef"))
    {
        int reverse = !strcmp(self->token->str, "ifndef");
        lexer_gettoken(self);
        if (self->token->type != TK_NAME)
            error(self->context, "macro name must be an identitifer");
        Macro *macro = preprocessor_find_macro(self->pp, self->token->str);
        int result = macro != NULL;
        if (reverse) result = !result;
        self->pp->condi_result[++self->pp->cr_pos] = result;
        self->pp->condi_pre[++self->pp->cp_pos] = head;
        FOLLOWINGTOKEN;
    }
    else if (!strcmp(self->token->str, "else"))
    {
        if (self->pp->condi_result[self->pp->cr_pos] == 0) // 上一个条件结果为0
        {
            head = self->pp->condi_pre[self->pp->cp_pos];
            CONNECT_HEAD(head, self->token);
            self->pp->condi_result[self->pp->cr_pos] = 1; // 当前条件结果为1
        }
        else
            self->pp->condi_result[self->pp->cr_pos] = 0;
        self->pp->condi_pre[self->pp->cp_pos] = head;
        FOLLOWINGTOKEN;
    }
    else if (!strcmp(self->token->str, "elif"))
    {
        error(self->context, "incomplete");
    }
    else if (!strcmp(self->token->str, "elifdef")
             || !strcmp(self->token->str, "elifndef"))
    {
        int reverse = !strcmp(self->token->str, "elifndef");
        lexer_gettoken(self);
        if (self->token->type != TK_NAME)
            error(self->context, "macro name must be an identitifer");
        if (self->pp->condi_result[self->pp->cr_pos] == 0) // 上一个条件结果为0
        {
            head = self->pp->condi_pre[self->pp->cp_pos];
            CONNECT_HEAD(head, self->token);

            // 只有在上一个条件不成立的情况下才会进行判断
            Macro *macro = preprocessor_find_macro(self->pp, self->token->str);
            int result = macro != NULL;
            if (reverse) result = !result;
            self->pp->condi_result[self->pp->cr_pos] = result;
        }
        else
            self->pp->condi_result[self->pp->cr_pos] = 0;
        self->pp->condi_pre[self->pp->cp_pos] = head;
        FOLLOWINGTOKEN;
    }
    else if (!strcmp(self->token->str, "endif"))
    {
        if (self->pp->cr_pos < 0) error(self->context, "#endif without #if");
        if (self->pp->condi_result[self->pp->cr_pos] == 0)
        {
            head = self->pp->condi_pre[self->pp->cp_pos];
            CONNECT_HEAD(head, self->token);
        }
        self->pp->cr_pos--;
        self->pp->cp_pos--;
        FOLLOWINGTOKEN;
    }
    else if (!strcmp(self->token->str, "line"))
    {
        lexer_gettoken(self);
        if (self->token->type != TK_INTCONST)
            error(self->context,
                  "#line directive requires a positive integer argument");
        int new_line = atoi(self->token->str);
        if (new_line < 0)
            error(self->context,
                  "#line directive requires a positive integer argument");
        self->context.row = new_line;
        lexer_gettoken(self);
        if (self->token->type == TK_STRINGCONST)
        {
            self->context.filename = self->token->str;
            FOLLOWINGTOKEN;
        }
        else
            tail = self->token;
    }
    else if (!strcmp(self->token->str, "embed"))
    {
        error(self->context, "incomplete");
    }
    else if (!strcmp(self->token->str, "warning")
             || !strcmp(self->token->str, "error"))
    {
        int is_error = !strcmp(self->token->str, "error");
        FileContext context = self->context;
        char *msg = empty_string();

        lexer_gettoken(self);
        SAVE_FLAG;
        REMOVE_FLAG(self->flag, LF_SKIPSPACE);
        while (self->token->type != TK_NEWLINE && self->token->type != TK_END)
        {
            msg = add_string(msg, self->token->str);
            lexer_gettoken(self);
        }
        RESTORE_FLAG;
        FOLLOWINGTOKEN;
        if (is_error)
            error(context, msg);
        else
            warning(context, msg);
    }
    else if (!strcmp(self->token->str, "pragma"))
    {
        error(self->context, "incomplete");
    }
    else
        error(self->context, "invalid preprocessing directive");
    RESTORE_FLAG;
    //移除预处理指令的token序列
    if (head == NULL)
    {
        self->token_head = tail;
        tail->pre = NULL;
    }
    else
        CONNECT(head, tail);
    self->token = tail;
}

void lexer_expand_macro(Lexer *self)
{
    Macro *macro = self->pp->macros;
    while (macro != NULL)
    {
        Token *head = self->token->pre;
        Token *tk = self->token;
        if (strcmp(macro->name, self->token->str)) goto next_macro;
        MacroArg *macroarg = NULL;
        int arg_num = 0;
        lexer_gettoken(self);
        if (macro->parameters != NULL)
        {
            if (self->token->type != TK_LPAREN) goto next_macro;
            macroarg = lexer_get_macro_args(self, macro, &arg_num);
            if (macroarg == NULL) goto next_macro; //参数不匹配
            lexer_gettoken(self); //之前的self->token应该是TK_RPAREN
        }
        Token *tail =
            self->token; //此时的self->token应该是替换序列的后一个token

        Token *h = NULL;
        Token *p = h;
        Token *b = macro->body;
        while (b != NULL)
        {
            Token *t = token_copy(b);
            if (t->type == TK_NAME)
            {
                Token *k = macroarg_find(macroarg, t->str, arg_num);
                if (k != NULL)
                    t = token_copy(k);
                else
                    t->next = NULL;
            }
            else if (t->type == TK_HASH && t->next != NULL
                     && t->next->type == TK_NAME)
            {
                Token *k = macroarg_find(macroarg, t->next->str, arg_num);
                char *str = empty_string();
                if (k != NULL)
                {
                    while (k != NULL)
                    {
                        str = add_string(str, k->str);
                        k = k->next;
                    }
                }
                else
                    str = add_string(str, t->next->str);
                t->type = TK_STRINGCONST;
                t->next = NULL;
                t->str = str;
                b = b->next;
            }
            else if (t->type == TK_HASHHASH)
            {
                if (t->next == NULL)
                    error(self->context,
                          "'##' cannot appear at end of macro expansion");
                Token *left = p;
                Token *right;
                if (t->next->type != TK_NAME
                    || (right = macroarg_find(macroarg, t->next->str, arg_num))
                           == NULL)
                {
                    right = token_copy(t->next);
                    right->next = NULL;
                }

                char *code = empty_string();
                while (left != NULL)
                {
                    code = add_string(code, left->str);
                    left = left->next;
                }
                while (right != NULL)
                {
                    code = add_string(code, right->str);
                    right = right->next;
                }

                Lexer lexer;
                lexer_init(&lexer, NULL, self->context.filename);
                REMOVE_FLAG(lexer.flag, LF_SKIPSPACE);
                ADD_FLAG(lexer.flag, LF_SKIPPP);

                Line line;
                line.buf = code;
                line.pos = 0;
                line.pre = line.next = NULL;
                lexer.line = &line;

                lexer_gettoken(&lexer);
                while (lexer.token->type != TK_END)
                {
                    lexer.token->context.row += p->context.row - 1;
                    lexer.token->context.col += p->context.col - 1;
                    lexer_gettoken(&lexer);
                }
                lexer.token->pre->next = NULL;
                t = lexer.token_head;
                free(lexer.token);
                p = p->pre; //移除原先的p
                b = b->next;
            }
            else
                t->next = NULL;
            if (p == NULL)
            {
                h = p = t;
                t->pre = NULL;
            }
            else
            {
                p->next = t;
                t->pre = p;
                p = p->next;
            }
            while (p->next != NULL)
            {
                p->next = token_copy(p->next);
                p->next->pre = p;
                p = p->next;
            }
            b = b->next;
        }
        if (p != NULL) p->next = tail;
        if (h == NULL)
        {
            if (head == NULL)
                self->token_head = tail;
            else
                CONNECT(head, tail);
            self->token = tail;
        }
        else
        {
            if (head == NULL)
                self->token_head = h;
            else
                CONNECT(head, h);
            self->token = h;
        }
        break;
    next_macro:
        self->token = tk;
        macro = macro->next;
    }
}

MacroArg *lexer_get_macro_args(Lexer *self, Macro *macro, int *arg_num)
{
    assert(self->token->type == TK_LPAREN);
    assert(macro->parameters != NULL);

    *arg_num = 0;
    Token *p = macro->parameters;
    while (p != NULL)
    {
        (*arg_num)++;
        p = p->next;
    }

    MacroArg *macroarg = malloc(sizeof(MacroArg) * (*arg_num));
    int i = 0;
    p = macro->parameters;
    while (p != NULL)
    {
        if (p->type == TK_ELLIPSIS)
        {
            macroarg[i].param = "__VA_ARGS__";
            macroarg[i].is_va_arg = 1;
        }
        else
        {
            macroarg[i].param = p->str;
            macroarg[i].is_va_arg = 0;
        }
        macroarg[i].arg = NULL;
        i++;
        p = p->next;
    }

    SAVE_FLAG;
    REMOVE_FLAG(self->flag, LF_SKIPSPACE);
    ADD_FLAG(self->flag, LF_SKIPPP);
    i = 0;
    lexer_gettoken(self);
    while (self->token->type != TK_RPAREN && self->token->type != TK_END)
    {
        int paren_match = 1;
        //不能破坏原来的token连接关系, 因为获取参数可能会失败
        Token *h = token_copy(self->token);
        h->next = NULL;
        p = h;
        lexer_gettoken(self);
        while (1)
        {
            switch (self->token->type)
            {
            case TK_LPAREN: paren_match++; break;
            case TK_RPAREN:
                if (--paren_match == 0) goto arg_got;
                break;
            case TK_COMMA:
                if (paren_match == 1) goto arg_got;
                break;
            case TK_END: return NULL; //参数匹配失败
            }
            p->next = token_copy(self->token);
            p->next->pre = p;
            p = p->next;
            p->next = NULL;
            lexer_gettoken(self);
        }
    arg_got:
        //去除首尾的空白字符
        if (p->type == TK_SPACE) p->pre->next = NULL;
        if (h->type == TK_SPACE) h = h->next;
        //将中间的所有空白替换成一个空格
        p = h->next;
        while (p != NULL)
        {
            if (p->type == TK_SPACE) p->str = " ";
            p = p->next;
        }

        if (!macroarg[i].is_va_arg)
            macroarg[i++].arg = h;
        else
        {
            if (macroarg[i].arg == NULL)
                macroarg[i].arg = h;
            else
            {
                p = macroarg[i].arg;
                while (p->next != NULL) p = p->next;
                p->next = h;
                h->pre = p;
            }
            if (self->token->type == TK_COMMA)
            {
                p = macroarg[i].arg;
                while (p->next != NULL) p = p->next;
                p->next = token_copy(self->token);
                p->next->pre = p;
            }
        }
        if (self->token->type == TK_RPAREN) break;
        lexer_gettoken(self);
    }
    RESTORE_FLAG;
    //参数数量不匹配
    if (i < *arg_num && !macroarg[(*arg_num) - 1].is_va_arg) return NULL;
    return macroarg;
}

/*
调用该函数时self->token应该是include指令的最后一个token
函数执行完后self->token应该是包含文件的第一个token
*/
void lexer_include(Lexer *self, char *filename, int include_std)
{
    Token *tail = self->token->next;
    for (int i = -1; i < self->pp->ip_len; i++)
    {
        char *filepath;
        if (i == -1 && !include_std)
            filepath =
                path_join(path_get_basename(self->context.filename), filename);
        else
        {
            if (i == -1) i++;
            filepath = path_join(self->pp->include_paths[i], filename);
        }
        FILE *file = fopen(filepath, "r");
        if (file != NULL)
        {
            Lexer lexer;
            lexer_init(&lexer, file, filepath);
            lexer.pp = self->pp;
            lexer_gettoken(&lexer);
            while (lexer.token->type != TK_END) lexer_gettoken(&lexer);
            lexer.token->pre->next = tail; // 去除最后的TK_END
            tail->pre = lexer.token->pre;
            self->token = lexer.token_head;
            return;
        }
    }
    error(self->context, "'%s' file not found", filename);
}