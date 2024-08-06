#include <setjmp.h>
#include <stdarg.h>
#include <stdio.h>

#include "error.h"
#include "exception.h"

void error(FileContext context, char *format, ...)
{
    va_list args;
    va_start(args, format);
    verror(context, format, args);
    va_end(args);
}

void verror(FileContext context, char *format, va_list args)
{
    printf("<%s:%d:%d>: error: ", context.filename, context.row, context.col);
    vprintf(format, args);
    printf("\n");
    longjmp(env, 1);
}

void errora(ASTContext astcontext, char *format, ...)
{
    FileContext context;
    context.filename = astcontext.filename;
    context.row = astcontext.s_row;
    context.col = astcontext.s_col;
    context.line = astcontext.line;

    va_list args;
    va_start(args, format);
    verror(context, format, args);
    va_end(args);
}