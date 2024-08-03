#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "stringutil.h"

char *empty_string()
{
    char *s = (char *)malloc(sizeof(char));
    s[0] = '\0';
    return s;
}

/*在原字符串上添加字符*/
char *add_char(char *str, char ch)
{
    size_t n = strlen(str) + 1; // 包括\0
    str = (char *)realloc(str, n + 1);
    str[n - 1] = ch;
    str[n] = '\0';
    return str;
}

char *add_string(char *s1, char *s2)
{
    size_t n = strlen(s1) + strlen(s2) + 1;
    s1 = (char *)realloc(s1, n + 1);
    strcat(s1, s2);
    s1[n] = '\0';
    return s1;
}

char *repr(char *s)
{
    char *p = empty_string();
    p = add_char(p, '"');
    while ((*s) != '\0')
    {
        switch (*s)
        {
        case '"':
            p = add_string(p, "\\\"");
            break;
        case '\\':
            p = add_string(p, "\\\\");
            break;
        case '\a':
            p = add_string(p, "\\a");
            break;
        case '\b':
            p = add_string(p, "\\b");
            break;
        case '\f':
            p = add_string(p, "\\f");
            break;
        case '\n':
            p = add_string(p, "\\n");
            break;
        case '\r':
            p = add_string(p, "\\r");
            break;
        case 't':
            p = add_string(p, "\\t");
            break;
        case 'v':
            p = add_string(p, "\\b");
            break;
        default:
            p = add_char(p, *s);
        }
        s++;
    }
    p = add_char(p, '"');
    return p;
}

char *path_get_basename(char *path)
{
    char *t = strrchr(path, '/');
    char *basename = (char *)malloc(t - path + 1);
    strncpy(basename, path, t - path);
    basename[t - path] = '\0';
    return basename;
}

char *path_join(char *p1, char *p2)
{
    char *s = empty_string();
    s = add_string(s, p1);
    s = add_char(s, '/');
    s = add_string(s, p2);
    return s;
}