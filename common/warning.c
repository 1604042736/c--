#include <stdio.h>
#include <stdarg.h>

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