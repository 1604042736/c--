#include "lexer.h"
#include "exception.h"
#include "parser.h"

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
    Parser parser;
    lexer_init(&lexer, file, "../test.txt");
    if (setjmp(env) == 0)
    {
        parser_init(&parser, &lexer);
        AST *ast = parser_start(&parser);
        ast_print(ast, 0);
    }
    fclose(file);
}