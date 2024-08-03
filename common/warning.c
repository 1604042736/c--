#include <stdio.h>
#include <stdarg.h>

#include "warning.h"

void warning(FileContext context, char *format, ...)
{
    printf("<%s:%d:%d>: warning: ", context.filename, context.row, context.col);
    va_list args;
    va_start(args, format);
    printf(format, args);
    va_end(args);
    printf("\n");
}