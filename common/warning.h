#ifndef __WARNING_H__
#define __WARNING_H__

#include <stdarg.h>

#include "ast.h"
#include "filecontext.h"

#ifdef __cplusplus
extern "C" {
#endif

void warning(FileContext, char *, ...);
void vwarning(FileContext, char *, va_list args);
void warninga(ASTContext, char *, ...);

#ifdef __cplusplus
}
#endif

#endif