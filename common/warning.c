#include <stdarg.h>
#include <stdio.h>

#include "warning.h"

void warning(FileContext context, char *format, ...)
{
    va_list args;
    va_start(args, format);
    vwarning(context, format, args);
    va_end(args);
}

void vwarning(FileContext context, char *format, va_list args)
{
    printf("<%s:%d:%d>: warning: ", context.filename, context.row, context.col);
    vprintf(format, args);
    printf("\n");
}

void warninga(ASTContext astcontext, char *format, ...)
{
    FileContext context;
    context.filename = astcontext.filename;
    context.row = astcontext.s_row;
    context.col = astcontext.s_col;
    context.line = astcontext.line;

    va_list args;
    va_start(args, format);
    vwarning(context, format, args);
    va_end(args);
}