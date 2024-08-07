#include "declanalyzer.h"
#include "error.h"
#include "exception.h"
#include "lexer.h"
#include "parser.h"

jmp_buf env;

int main()
{
    char *filename = "../test.txt";
    FILE *file = fopen(filename, "r");
    if (file == NULL)
    {
        printf("cannot open file: %s\n", filename);
        return 0;
    }
    Lexer lexer;
    Parser parser;
    lexer_init(&lexer, file, filename);
    if (setjmp(env) == 0)
    {
        /*do
        {
            lexer_gettoken(&lexer);
            printf("%s\n", repr(lexer.token->str));
        } while (lexer.token->type != TK_END);
        PRINT_TOKEN_LIST(lexer.token_head);
        return 0;*/
        parser_init(&parser, &lexer);
        AST *ast = parser_start(&parser);
        // ast_print(ast, 0);
        for (int i = 0; i < parser.error_num; i++)
            error(parser.errors[i].context, parser.errors[i].msg);

        DeclAnalyzer declanalyzer;
        declanalyzer_init(&declanalyzer);
        declanalyzer_analyze(&declanalyzer, ast);
        ast_print(ast, 0);
    }
    fclose(file);
}