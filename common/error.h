#ifndef __ERROR_H__
#define __ERROR_H__

#include "filecontext.h"

#ifdef __cplusplus
extern "C"
{
#endif

    void error(FileContext, char *, ...);

#ifdef __cplusplus
}
#endif

#endif