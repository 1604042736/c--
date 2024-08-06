#ifndef __PARSER_H__
#define __PARSER_H__

#include "ast.h"
#include "lexer.h"

#ifdef __cplusplus
extern "C" {
#endif

#define MAX_ERROR_NUM 100

typedef struct {
    Lexer *lexer;
    struct {
        char *msg;
        FileContext context;
    } errors[MAX_ERROR_NUM];
    int error_num;
} Parser;

Parser *parser_new();
void parser_init(Parser *, Lexer *);

int parser_match(Parser *, TokenType actual, TokenType expected);

AST *parser_primary_expression(Parser *);
AST *parser_postfix_expression(Parser *);
AST *parser_argument_expression_list(Parser *);
AST *parser_unary_expression(Parser *);
AST *parser_cast_expression(Parser *);
AST *parser_multiplicative_expression(Parser *);
AST *parser_addtive_expression(Parser *);
AST *parser_shift_expression(Parser *);
AST *parser_relational_expression(Parser *);
AST *parser_equality_expression(Parser *);
AST *parser_and_expression(Parser *);
AST *parser_exclusive_or_expression(Parser *);
AST *parser_inclusive_or_expression(Parser *);
AST *parser_logical_and_expression(Parser *);
AST *parser_logical_or_expression(Parser *);
AST *parser_conditional_expression(Parser *);
AST *parser_assignment_expression(Parser *);
AST *parser_expression(Parser *);
AST *parser_constant_expression(Parser *);
AST *parser_declaration(Parser *);
int parser_is_declaration(Parser *);
AST *parser_declaration_specifier(Parser *);
AST *parser_init_declaratior_list(Parser *);
AST *parser_init_declarator(Parser *);
AST *parser_storage_class_specifier(Parser *);
int parser_is_storage_class_specifier(Parser *);
AST *parser_type_specifer(Parser *);
int parser_is_type_specifer(Parser *);
AST *parser_struct_or_union_specifer(Parser *);
AST *parser_struct_declaration_list(Parser *);
AST *parser_struct_declaration(Parser *);
AST *parser_specifier_qualifier_list(Parser *);
AST *parser_struct_declarator_list(Parser *);
AST *parser_struct_declarator(Parser *);
AST *parser_enum_specifier(Parser *);
AST *parser_enumerator_list(Parser *);
AST *parser_enumerator(Parser *);
AST *parser_type_qualifier(Parser *);
int parser_is_type_qualifier(Parser *);
AST *parser_parameter_declaration(Parser *);
AST *parser_declarator(Parser *);
AST *parser_abstract_declarator(Parser *);
AST *parser_direct_declarator(Parser *);
AST *parser_direct_abstract_delarator(Parser *);
AST *parser_pointer(Parser *);
int parser_is_pointer(Parser *);
AST *parser_type_qualifier_list(Parser *);
int parser_is_type_qualifier_list(Parser *);
AST *parser_parameter_type_list(Parser *);
AST *parser_parameter_list(Parser *);
AST *parser_type_name(Parser *);
AST *parser_initializer(Parser *);
AST *parser_initializer_list(Parser *);
AST *parser_declaration_list(Parser *);
AST *parser_statement(Parser *);
AST *parser_labeled_statement(Parser *);
AST *parser_compound_statement(Parser *);
AST *parser_expression_statement(Parser *);
AST *parser_selection_statement(Parser *);
AST *parser_iteration_statement(Parser *);
AST *parser_jump_statement(Parser *);
AST *parser_translation_unit(Parser *);
AST *parser_external_declaration(Parser *);
AST *parser_functionn_definition(Parser *);
AST *parser_start(Parser *);

#ifdef __cplusplus
}
#endif

#endif