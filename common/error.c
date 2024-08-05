#include <stdarg.h>
#include <stdio.h>
#include <setjmp.h>

#include "exception.h"
#include "error.h"

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