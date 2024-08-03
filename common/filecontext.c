#include "filecontext.h"

void filecontext_init(FileContext *self, FILE *file, char *filename, int row, int col)
{
    self->file = file;
    self->filename = filename;
    self->row = row;
    self->col = col;
    self->l_row = row;
}