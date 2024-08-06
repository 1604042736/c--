#ifndef __ERROR_H__
#define __ERROR_H__

#include <stdarg.h>

#include "ast.h"
#include "filecontext.h"


#ifdef __cplusplus
extern "C" {
#endif

void error(FileContext, char *, ...);
void verror(FileContext, char *, va_list args);
void errora(ASTContext, char *, ...);

#ifdef __cplusplus
}
#endif

#endif