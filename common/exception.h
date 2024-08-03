#ifndef __EXCEPTION_H__
#define __EXCEPTION_H__

#include <setjmp.h>

#ifdef __cplusplus
extern "C"
{
#endif

    extern jmp_buf env;

#ifdef __cplusplus
}
#endif

#endif