#include "lexer.h"
#include "exception.h"

jmp_buf env;

int main()
{
    FILE *file = fopen("../test.txt", "r");
    if (file == NULL)
    {
        printf("Can't open file\n");
        return 0;
    }
    Lexer lexer;
    lexer_init(&lexer, file, "../test.txt");
    if (setjmp(env) == 0)
    {
        lexer_gettoken(&lexer);
        while (lexer.token->type != TK_END)
            lexer_gettoken(&lexer);
        Token *p = lexer.token_head;
        while (p != NULL)
        {
            if (p->type < TOKEN_NUM)
                printf("%s\t", token_names[p->type]);
            printf("%s\t%s\t%d\t%d\n",
                   p->str,
                   p->context.filename,
                   p->context.row,
                   p->context.col);
            p = p->next;
        }
    }
    fclose(file);
}