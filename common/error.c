#include <stdarg.h>
#include <stdio.h>
#include <setjmp.h>

#include "exception.h"
#include "error.h"

void error(FileContext context, char *format, ...)
{
    printf("<%s:%d:%d>: error: ", context.filename, context.row, context.col);
    va_list args;
    va_start(args, format);
    printf(format, args);
    va_end(args);
    printf("\n");
    longjmp(env, 1);
}