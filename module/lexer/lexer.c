#include <stdlib.h>
#include <ctype.h>
#include <string.h>
#include <stdarg.h>

#include "lexer.h"
#include "warning.h"
#include "stringutil.h"
#include "error.h"

Lexer *lexer_new()
{
    return (Lexer *)malloc(sizeof(Lexer));
}

void lexer_init(Lexer *self, FILE *file, char *filename)
{
    filecontext_init(&self->context, file, filename, 1, 0);
    self->token = NULL;
    self->token_head = NULL;
    self->lines = NULL;
    self->pp = preprocessor_new();
    preprocessor_init(self->pp);
    self->eof = 0; // file==NULL的情况是给预处理器专门使用的
    self->ignore_pp = 0;
    self->ignore_space = 1;
    self->merge_row = 0;
}

Line *line_new()
{
    return (Line *)malloc(sizeof(Line));
}

void line_init(Line *self, Lexer *lexer)
{
    self->pre = self->next = NULL;
    memset(self->buf, '\0', sizeof(self->buf));
    if (lexer->context.file != NULL)
        fgets(self->buf, BUF_SIZE, lexer->context.file);
    else
        lexer->eof = 1;
    self->pos = 0;
}

void lexer_getch(Lexer *self)
{
    if (self->lines == NULL)
    {
        self->lines = line_new();
        line_init(self->lines, self);
        self->context.line = self->lines->buf;
    }
    while (self->lines->pos >= strlen(self->lines->buf))
    {
        if (feof(self->context.file) || self->context.file == NULL)
        {
            self->ch = EOF;
            self->eof = 1;
            return;
        }
        if (self->lines->pos > 0 && self->lines->buf[self->lines->pos - 1] == '\n') // 有可能出现一行没读完的情况
        {
            self->context.row++;
            if (!self->merge_row)
                self->context.l_row++;
            else
                self->merge_row = 0;
            self->context.col = 0;
        }
        if (self->lines->next != NULL)
            self->lines = self->lines->next;
        else
        {
            Line *new_line = line_new();
            line_init(new_line, self);
            new_line->pre = self->lines;
            self->lines->next = new_line;
            self->lines = self->lines->next;
        }
        self->context.line = self->lines->buf;
    }
    self->context.col++;
    self->ch = self->lines->buf[self->lines->pos++];
    if (self->ch == '\\')
    {
        int n = strlen(self->lines->buf) - self->lines->pos;
        char *s = (char *)malloc(n + 1);
        strncpy(s, self->lines->buf + self->lines->pos, n);
        s[n] = '\0';
        if (!strcmp(s, "\n") || !strcmp(s, "\r\r"))
        {
            self->merge_row = 1;                         // 合并这两行
            self->lines->pos = strlen(self->lines->buf); // 强制结束这一行
            lexer_getch(self);
        }
        free(s);
    }
}

void lexer_ungetch(Lexer *self)
{
    if (self->eof)
        return;
    self->context.col--;
    if (self->lines->pos == 0)
    {
        if (self->lines->pre != NULL)
            self->lines = self->lines->pre;
        self->lines->pos = strlen(self->lines->buf) - 1;
        self->context.col = self->lines->pos + 1;
        self->context.line = self->lines->buf;
        if (self->lines->buf[self->lines->pos] == '\n') // 有可能出现一行没有读完的情况
        {
            self->context.row--;
            self->context.l_row--;
        }
    }
    else
        self->lines->pos--;
    self->ch = self->lines->buf[self->lines->pos];
}

char lexer_get_escape(Lexer *self, char c)
{
    switch (c)
    {
    case '\'':
        return '\'';
    case '"':
        return '"';
    case '\\':
        return '\\';
    case 'a':
        return '\a';
    case 'b':
        return '\b';
    case 'f':
        return '\f';
    case 'n':
        return '\n';
    case 'r':
        return '\r';
    case 't':
        return '\t';
    case 'v':
        return '\v';
    case '0':
        return '\0';
    default:
        warning(self->context, "unknown escape sequence '\\%c'\n", c);
        return c;
    }
}

void lexer_gettoken(Lexer *self)
{
#define TOKEN(type, str) token_init(self->token, type, context, str)
    if (self->token != NULL && self->token->next != NULL)
    {
        self->token = self->token->next;
        goto process;
    }
    Token *pre = self->token;
    self->token = token_new();
    lexer_getch(self);
    if (self->ignore_space)
    {
        while (isspace(self->ch) && self->ch != EOF)
            lexer_getch(self);
    }
    FileContext context = self->context;
    if (self->ch == EOF)
        TOKEN(TK_END, "<eof>");
    else if (isalpha(self->ch) || self->ch == '_')
    {
        char *str = empty_string();
        str = add_char(str, self->ch);
        lexer_getch(self);
        while (isalpha(self->ch) || isdigit(self->ch) || self->ch == '_')
        {
            str = add_char(str, self->ch);
            lexer_getch(self);
        }
        lexer_ungetch(self);
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
    }
    else if (isdigit(self->ch))
    {
        TokenType type = TK_INTCONST;
        char *str = empty_string();
        str = add_char(str, self->ch);
        lexer_getch(self);
        while (isdigit(self->ch))
        {
            str = add_char(str, self->ch);
            lexer_getch(self);
        }
        if (self->ch == '.')
        {
            str = add_char(str, self->ch);
            lexer_getch(self);
            while (isdigit(self->ch))
            {
                str = add_char(str, self->ch);
                lexer_getch(self);
            }
            type = TK_FLOATCONST;
        }
        lexer_ungetch(self);
        TOKEN(type, str);
    }
    else if (self->ch == '[')
        TOKEN(TK_LSQUARE, "[");
    else if (self->ch == ']')
        TOKEN(TK_RSQUARE, "]");
    else if (self->ch == '(')
        TOKEN(TK_LPAREN, "(");
    else if (self->ch == ')')
        TOKEN(TK_RPAREN, ")");
    else if (self->ch == '{')
        TOKEN(TK_LBRACE, "{");
    else if (self->ch == '}')
        TOKEN(TK_RBRACE, "}");
    else if (self->ch == '.')
    {
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
    }
    else if (self->ch == '&')
    {
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
    }
    else if (self->ch == '*')
    {
        lexer_getch(self);
        if (self->ch == '=')
            TOKEN(TK_STAREQUAL, "*=");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_STAR, "*");
        }
    }
    else if (self->ch == '+')
    {
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
    }
    else if (self->ch == '-')
    {
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
    }
    else if (self->ch == '~')
        TOKEN(TK_TILDE, "~");
    else if (self->ch == '!')
    {
        lexer_getch(self);
        if (self->ch == '=')
            TOKEN(TK_EXCLAIMEQUAL, "!=");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_EXCLAIM, "!");
        }
    }
    else if (self->ch == '/')
    {
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
            TOKEN(TK_COMMENT, str);
        }
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_SLASH, "/");
        }
    }
    else if (self->ch == '%')
    {
        lexer_getch(self);
        if (self->ch == '=')
            TOKEN(TK_PERCENTEQUAL, "%=");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_PERCENT, "%");
        }
    }
    else if (self->ch == '<')
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
    else if (self->ch == '>')
    {
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
    }
    else if (self->ch == '^')
    {
        lexer_getch(self);
        if (self->ch == '=')
            TOKEN(TK_CARETEQUAL, "^=");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_CARET, "^");
        }
    }
    else if (self->ch == '|')
    {
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
    }
    else if (self->ch == '?')
        TOKEN(TK_QUESTION, "?");
    else if (self->ch == ':')
        TOKEN(TK_COLON, ":");
    else if (self->ch == ';')
        TOKEN(TK_SEMI, ";");
    else if (self->ch == '=')
    {
        lexer_getch(self);
        if (self->ch == '=')
            TOKEN(TK_EQUALEQUAL, "==");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_EQUAL, "=");
        }
    }
    else if (self->ch == ',')
        TOKEN(TK_COMMA, ",");
    else if (self->ch == '\'')
    {
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
    }
    else if (self->ch == '"')
    {
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
    }
    else if (self->ch == '#')
    {
        lexer_getch(self);
        if (self->ch == '#')
            TOKEN(TK_HASHHASH, "##");
        else
        {
            lexer_ungetch(self);
            TOKEN(TK_HASH, "#");
        }
    }
    else
    {
        char *str = (char *)malloc(sizeof(char) * 2);
        str[0] = self->ch;
        str[1] = '\0';
        TOKEN(TK_UNKNOWN, str);
    }
    self->token->pre = pre;
    if (pre != NULL)
        pre->next = self->token;
    if (self->token_head == NULL)
        self->token_head = self->token;
process:
    while (self->token->type == TK_COMMENT)
        lexer_gettoken(self);
    while (self->token->type == TK_HASH && !self->ignore_pp)
        lexer_handle_directive(self);
    Token *tk = self->token;
    while (self->token->type == TK_NAME && !self->ignore_pp)
    {
        lexer_expand_macro(self);
        if (tk == self->token) // 没有替换
            break;
        tk = self->token;
    }
    // 连接相邻的字符串字面量
    if (self->token->type == TK_STRINGCONST)
    {
        lexer_gettoken(self);
        if (self->token->type == TK_STRINGCONST)
        {
            lexer_ungettoken(self);
            char *str = empty_string();
            str = add_string(str, self->token->str);
            str = add_string(str, self->token->next->str);
            token_init(self->token, TK_STRINGCONST, self->token->context, str);
            self->token->next->next->pre = self->token;
            self->token->next = self->token->next->next;
        }
        else
            lexer_ungettoken(self);
    }
}

void lexer_ungettoken(Lexer *self)
{
    if (self->token != NULL && self->token->pre != NULL)
        self->token = self->token->pre;
}

void lexer_match(Lexer *self, TokenType actual, TokenType expected, char *format, ...)
{
    if (actual != expected)
    {
        va_list args;
        va_start(args, format);
        error(self->context, format, args);
        va_end(args);
    }
}

#define CONNECT_HEAD(head, end)     \
    do                              \
    {                               \
        if (head != NULL)           \
            CONNECT(head, end);     \
        else                        \
            self->token_head = end; \
    } while (0)
void lexer_handle_directive(Lexer *self)
{
    int _ignore_pp = self->ignore_pp;
    self->ignore_pp = 1;
    Token *head = self->token->pre;
    int l_row = self->context.l_row;
    FileContext context = self->context;
    lexer_gettoken(self);
    if (self->context.l_row != l_row)
        goto end;
    if (!strcmp(self->token->str, "define")) // 不完全符合标准
    {
        lexer_gettoken(self);
        lexer_match(self, self->token->type, TK_NAME, "macro name must be an identitifer");
        if (self->context.l_row != l_row)
            error(context, "macro name missing");

        char *name = self->token->str;
        lexer_gettoken(self);
        Token *parameters = NULL;
        if (self->token->type == TK_LPAREN && self->context.l_row == l_row)
        {
            lexer_gettoken(self);
            if (self->token->type != TK_RPAREN && self->context.l_row == l_row)
            {
                if (self->token->type != TK_NAME && self->token->type != TK_ELLIPSIS)
                    error(self->context, "invalid token in macro parameter list");
                parameters = token_copy(self->token);
                parameters->pre = NULL;
                Token *p = parameters;
                lexer_gettoken(self);
                while (self->token->type != TK_RPAREN && self->context.l_row == l_row)
                {
                    lexer_match(self, self->token->type, TK_COMMA, "expected comma in macro parameter list");
                    lexer_gettoken(self);
                    if (self->token->type != TK_NAME && self->token->type != TK_ELLIPSIS)
                        error(self->context, "invalid token in macro parameter list");
                    if (self->context.l_row != l_row)
                        break;
                    p->next = token_copy(self->token);
                    p->next->pre = p;
                    p = p->next;
                    lexer_gettoken(self);
                }
            }
            if (self->token->type == TK_RPAREN && self->context.l_row != l_row)
                error(context, "missing ')' in macro parameter list");
            if (self->context.l_row == l_row)
                lexer_gettoken(self);
        }
        Token *body = NULL;
        if (self->context.l_row == l_row)
        {
            body = token_copy(self->token);
            Token *p = body;
            p->pre = NULL;
            lexer_gettoken(self);
            while (self->context.l_row == l_row && (self->token->type != TK_UNKNOWN || self->token->str[0] != '\n'))
            {
                p->next = token_copy(self->token);
                p->next->pre = p;
                p = p->next;
                lexer_gettoken(self);
            }
            if (self->context.l_row == l_row)
                lexer_gettoken(self);
        }

        Macro *macro = macro_new();
        macro_init(macro, name, parameters, body);
        if (self->pp->macros == NULL)
            self->pp->macros = macro;
        else
        {
            Macro *p = self->pp->macros;
            while (p->next != NULL)
                p = p->next;
            p->next = macro;
            macro->pre = p;
        }
    }
    else if (!strcmp(self->token->str, "undef"))
    {
        lexer_gettoken(self);
        lexer_match(self, self->token->type, TK_NAME, "macro name must be an identitifer");
        if (self->context.l_row != l_row)
            error(context, "macro name missing");
        Macro *p = self->pp->macros;
        while (p != NULL)
        {
            if (!strcmp(p->name, self->token->str))
            {
                if (p->next != NULL)
                    p->next->pre = p->pre;
                if (p->pre != NULL)
                    p->pre->next = p->next;
                else
                    self->pp->macros = p->next;
                break;
            }
            p = p->next;
        }
        lexer_gettoken(self);
    }
    else if (!strcmp(self->token->str, "include"))
    {
        lexer_gettoken(self);
        char *filename;
        int include_std;
        if (self->token->type == TK_STRINGCONST && self->context.l_row == l_row)
        {
            include_std = 0;
            filename = self->token->str;
        }
        else if (self->token->type == TK_LESS && self->context.l_row == l_row)
        {
            include_std = 1;
            filename = empty_string();
            lexer_gettoken(self);
            int _ignore_space = self->ignore_space;
            self->ignore_space = 0;

            while (self->token->type != TK_GREATER && self->context.l_row == l_row)
            {
                filename = add_string(filename, self->token->str);
                lexer_gettoken(self);
            }
            if (self->context.l_row != l_row)
                error(context, "expected \"FILENAME\" or <FILENAME>");

            self->ignore_space = _ignore_space;
        }
        else
            error(self->context.l_row == l_row ? self->context : context, "expected \"FILENAME\" or <FILENAME>");
        lexer_include(self, filename, include_std);
    }
    else if (!strcmp(self->token->str, "if"))
    {
        error(self->context, "incomplete");
    }
    else if (!strcmp(self->token->str, "ifdef") || !strcmp(self->token->str, "ifndef"))
    {
        int reverse = !strcmp(self->token->str, "ifndef");
        lexer_gettoken(self);
        lexer_match(self, self->token->type, TK_NAME, "macro name must be an identitifer");
        if (self->context.l_row != l_row)
            error(context, "macro name missing");
        Macro *macro = preprocessor_find_macro(self->pp, self->token->str);
        int result = macro != NULL;
        if (reverse)
            result = !result;
        self->pp->condi_result[++self->pp->cr_pos] = result;
        self->pp->condi_pre[++self->pp->cp_pos] = head;
        lexer_gettoken(self);
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
        lexer_gettoken(self);
    }
    else if (!strcmp(self->token->str, "elif"))
    {
        error(self->context, "incomplete");
    }
    else if (!strcmp(self->token->str, "elifdef") || !strcmp(self->token->str, "elifndef"))
    {
        int reverse = !strcmp(self->token->str, "elifndef");
        lexer_gettoken(self);
        lexer_match(self, self->token->type, TK_NAME, "macro name must be an identitifer");
        if (self->context.l_row != l_row)
            error(context, "macro name missing");
        if (self->pp->condi_result[self->pp->cr_pos] == 0) // 上一个条件结果为0
        {
            head = self->pp->condi_pre[self->pp->cp_pos];
            CONNECT_HEAD(head, self->token);

            // 只有在上一个条件不成立的情况下才会进行判断
            Macro *macro = preprocessor_find_macro(self->pp, self->token->str);
            int result = macro != NULL;
            if (reverse)
                result = !result;
            self->pp->condi_result[self->pp->cr_pos] = result;
        }
        else
            self->pp->condi_result[self->pp->cr_pos] = 0;
        self->pp->condi_pre[self->pp->cp_pos] = head;
        lexer_gettoken(self);
    }
    else if (!strcmp(self->token->str, "endif"))
    {
        if (self->pp->cr_pos < 0)
            error(self->context, "#endif without #if");
        if (self->pp->condi_result[self->pp->cr_pos] == 0)
        {
            head = self->pp->condi_pre[self->pp->cp_pos];
            CONNECT_HEAD(head, self->token);
        }
        self->pp->cr_pos--;
        self->pp->cp_pos--;
        lexer_gettoken(self);
    }
    else if (!strcmp(self->token->str, "line"))
    {
        lexer_gettoken(self);
        lexer_match(self, self->token->type, TK_INTCONST, "#line directive requires a positive integer argument");
        int new_line = atoi(self->token->str);
        if (new_line < 0 || self->token->context.l_row != l_row)
            error(new_line < 0 ? self->context : context, "#line directive requires a positive integer argument");
        self->context.row = new_line;
        lexer_gettoken(self);
        if (self->token->type == TK_STRINGCONST && self->token->context.l_row == l_row)
        {
            self->context.filename = self->token->str;
            lexer_gettoken(self);
        }
    }
    else if (!strcmp(self->token->str, "embed"))
    {
        error(self->context, "incomplete");
    }
    else if (!strcmp(self->token->str, "warning") || !strcmp(self->token->str, "error"))
    {
        int is_error = !strcmp(self->token->str, "error");
        FileContext context = self->context;
        char *msg = empty_string();

        lexer_gettoken(self);
        int _ignore_space = self->ignore_space;
        self->ignore_space = 0;
        while (self->context.l_row == l_row && (self->token->type != TK_UNKNOWN || self->token->str[0] != '\n'))
        {
            msg = add_string(msg, self->token->str);
            lexer_gettoken(self);
        }
        self->ignore_space = _ignore_space;
        if (self->context.l_row == l_row)
            lexer_gettoken(self);

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
        error(self->context, "invalid preprocessor directive: %s", self->token->str);
end:
    self->ignore_pp = _ignore_pp;
    // 此时self->token应该是预处理指令的最后一个token的后一个token
    CONNECT_HEAD(head, self->token);
}

/*
调用该函数时保证self->token->type==TK_NAME
同时self->token不一定是token链的最后一个
*/
void lexer_expand_macro(Lexer *self)
{
    static int expanding = 0; // 正在展开宏的数量
    static Token *tk = NULL;  // 第一个展开宏的前一个token
    if (!strcmp(self->token->str, "__LINE__"))
    {
        self->token->type = TK_INTCONST;
        self->token->str = (char *)malloc(11);
        self->token->str = itoa(self->context.row, self->token->str, 10);
        return;
    }
    if (!strcmp(self->token->str, "__FILE__"))
    {
        self->token->type = TK_STRINGCONST;
        self->token->str = self->context.filename;
        return;
    }
    Macro *macro = self->pp->macros;
    while (macro != NULL)
    {
        if (!strcmp(self->token->str, macro->name))
        {
            Token *head = self->token, *tail; // 与宏展开有关的token链首尾两个(不包括tail)
            if (++expanding == 1)
                tk = head->pre;
            int arg_num = 0;
            MacroArg *macroarg = NULL;
            lexer_gettoken(self);
            if (self->token->type == TK_LPAREN)
            {
                if ((macroarg = lexer_get_macro_args(self, macro, &arg_num)) == NULL) // 参数不匹配
                {
                    macro = macro->next;
                    lexer_ungettoken(self);
                    continue;
                }
                lexer_gettoken(self); // lexer_get_macro_args运行完后self->token->type==TK_RPAREN
            }
            tail = self->token;
            // 单方面断开与宏展开有关的token链与原token链
            tail->pre = NULL;
            head->pre->next = NULL;

            Token *p = head->pre;
            Token *r = macro->body;
            while (r != NULL) // 该循环与self无关
            {
                Token *t = r;
                if (t->type == TK_NAME)
                {
                    Token *q;
                    q = macroarg_find(macroarg, t->str, arg_num);
                    if (q != NULL)
                        t = token_copy(q);
                    else if (t->type == TK_NAME && !strcmp(t->str, "__VA_ARGS__"))
                    {
                        r = r->next;
                        continue;
                    }
                }
                else if (t->type == TK_HASH)
                {
                    Token *q;
                    if (t->next == NULL || t->next->type != TK_NAME || (q = macroarg_find(macroarg, t->next->str, arg_num)) == NULL)
                        error(self->context, "'#' is not followed by a macro parameter");
                    r = r->next;
                    char *str = empty_string();
                    while (q != NULL)
                    {
                        str = add_string(str, (q->type == TK_STRINGCONST ? repr(q->str) : q->str));
                        q = q->next;
                    }
                    t = token_new();
                    token_init(t, TK_STRINGCONST, r->context, str);
                }
                else if (t->type == TK_HASHHASH)
                {
                    if (t->next == NULL)
                        error(self->context, "'##' cannot appear at end of macro expansion");
                    r = r->next;
                    Token *a = p;
                    Token *b = t->next;
                    if (b->type == TK_NAME)
                    {
                        Token *q;
                        q = macroarg_find(macroarg, b->str, arg_num);
                        if (q != NULL)
                            b = token_copy(q);
                        else if (b->type == TK_NAME && !strcmp(b->str, "__VA_ARGS__")) // 忽略空的__VA_ARGS__的拼接
                        {
                            r = r->next;
                            continue;
                        }
                    }
                    char *code = empty_string();
                    code = add_string(code, a->str);
                    while (b != NULL)
                    {
                        code = add_string(code, b->type == TK_STRINGCONST ? repr(b->str) : b->str);
                        b = b->next;
                    }

                    Lexer lexer;
                    lexer_init(&lexer, NULL, self->context.filename);
                    lexer.ignore_space = 0; // 可能有宏嵌套

                    Line line;
                    strcpy(line.buf, code);
                    line.pos = 0;
                    line.pre = line.next = NULL;
                    lexer.lines = &line;

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
                    p = p->pre;
                }
                if (t == r)
                {
                    p->next = token_copy(t);
                    p->next->pre = p;
                    p->next->next = NULL;
                    p = p->next;
                }
                else
                {
                    while (t != NULL)
                    {
                        p->next = token_copy(t);
                        p->next->pre = p;
                        p->next->next = NULL;
                        p = p->next;
                        t = t->next;
                    }
                }

                r = r->next;
            }
            if (head->pre->next == NULL) // 说明宏没有进行替换
            {
                self->token = tail;
                self->token->pre = head->pre;
                head->pre->next = self->token;
            }
            else
            {
                self->token = head->pre->next;
                self->token->pre = head->pre;
                p->next = tail;
                tail->pre = p;
            }
            if (--expanding == 0)
            { // 去除空白token
                p = self->token;
                while (p != NULL)
                {
                    if (IS_SPACE_TOKEN(p))
                    {
                        p->pre->next = p->next;
                        p->next->pre = p->pre;
                    }
                    p = p->next;
                }
            }

            free(macroarg);
        }
        macro = macro->next;
    }
}

/*
获取宏参数
调用该函数时保证self->token->type==TK_LPAREN
param_num表示参数个数
*/
MacroArg *lexer_get_macro_args(Lexer *self, Macro *macro, int *arg_num)
{
    if (macro->parameters == NULL)
        return NULL;
    // 确定参数个数
    *arg_num = 0;
    Token *p = macro->parameters;
    while (p != NULL)
    {
        (*arg_num)++;
        p = p->next;
    }
    // 初始化形参
    MacroArg *macroarg = (MacroArg *)malloc(sizeof(MacroArg) * (*arg_num));
    int i = 0;
    p = macro->parameters;
    while (p != NULL)
    {
        macroarg[i].param = p->type != TK_ELLIPSIS ? p->str : "__VA_ARGS__";
        macroarg[i].arg = NULL;
        macroarg[i].is_va_arg = p->type == TK_ELLIPSIS;
        i++;
        p = p->next;
    }
    // 获取实参
    i = 0;
    lexer_gettoken(self);
    int _ignore_space = self->ignore_space;
    while (self->token->type != TK_RPAREN)
    {
        self->ignore_space = 0;
        p = token_copy(self->token);
        p->pre = NULL;

        Token *h = p;
        h->next = NULL;
        int paren_num = 1; // 用于括号匹配
        lexer_gettoken(self);
        while (1)
        {
            switch (self->token->type)
            {
            case TK_RPAREN:
                if (--paren_num == 0)
                    goto arg_got;
                break;
            case TK_COMMA:
                if (paren_num == 1)
                    goto arg_got;
                break;
            case TK_END:
                error(self->context, "file end while getting macro args");
            }
            h->next = token_copy(self->token);
            h->next->pre = h;
            h = h->next;
            h->next = NULL;
            lexer_gettoken(self);
        }
    arg_got:
        // 删除尾随空白字符
        while (IS_SPACE_TOKEN(h))
        {
            h->pre->next = NULL;
            h = h->pre;
        }
        if (macroarg[i].is_va_arg)
        {
            int first_in = 0;
            if (macroarg[i].arg == NULL)
            {
                macroarg[i].arg = p;
                first_in = 1;
            }
            Token *t = macroarg[i].arg;
            while (t->next != NULL)
                t = t->next;
            if (!first_in)
            {
                t->next = p;
                t->next->pre = t;
                t->next->next = NULL;
                t = t->next;
            }
            if (self->token->type == TK_COMMA)
            {
                t->next = token_copy(self->token);
                t->next->pre = t;
                t->next->next = NULL;
            }
        }
        else
            macroarg[i++].arg = p;

        if (IS_SPACE_TOKEN(self->token))
        {
            self->token->next->pre = self->token->pre;
            self->token = self->token->pre;
            self->token->next = self->token->next->next;
        }
        self->ignore_space = 1; // 实参从第一个非空白字符开始
        if (self->token->type == TK_RPAREN)
            break;
        lexer_gettoken(self);
    }
    self->ignore_space = _ignore_space;
    if (i < *arg_num && !macroarg[i].is_va_arg) // 参数个数不匹配
        return NULL;
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
            filepath = path_join(path_get_basename(self->context.filename), filename);
        else
        {
            if (i == -1)
                i++;
            filepath = path_join(self->pp->include_paths[i], filename);
        }
        FILE *file = fopen(filepath, "r");
        if (file != NULL)
        {
            Lexer lexer;
            lexer_init(&lexer, file, filepath);
            lexer_gettoken(&lexer);
            while (lexer.token->type != TK_END)
                lexer_gettoken(&lexer);
            lexer.token->pre->next = tail; // 去除最后的TK_END
            tail->pre = lexer.token->pre;
            self->token = lexer.token_head;
            return;
        }
    }
    error(self->context, "'%s' file not found", filename);
}