#!/usr/bin/env python3.8
# @generated by pegen from Grammar/compiler.gram

import ast
import sys
import tokenize

from typing import Any, Optional

from pegen.parser import memoize, memoize_left_rec, logger, Parser

from SyntaxTrees import *

# Keywords and soft keywords are listed at the end of the parser definition.
class GeneratedParser(Parser):

    @memoize
    def start(self) -> Optional[Any]:
        # start: statement? $
        mark = self._mark()
        if (
            (a := self.statement(),)
            and
            (_endmarker := self.expect('ENDMARKER'))
        ):
            return Program ( body = a )
        self._reset(mark)
        return None

    @memoize
    def body(self) -> Optional[Any]:
        # body: NEWLINE INDENT statement DEDENT
        mark = self._mark()
        if (
            (_newline := self.expect('NEWLINE'))
            and
            (_indent := self.expect('INDENT'))
            and
            (a := self.statement())
            and
            (_dedent := self.expect('DEDENT'))
        ):
            return a
        self._reset(mark)
        return None

    @memoize
    def statement(self) -> Optional[Any]:
        # statement: sentences*
        # nullable=True
        mark = self._mark()
        if (
            (_loop0_1 := self._loop0_1(),)
        ):
            return _loop0_1
        self._reset(mark)
        return None

    @memoize
    def sentences(self) -> Optional[Any]:
        # sentences: sentence NEWLINE | sentence
        mark = self._mark()
        if (
            (a := self.sentence())
            and
            (_newline := self.expect('NEWLINE'))
        ):
            return a
        self._reset(mark)
        if (
            (sentence := self.sentence())
        ):
            return sentence
        self._reset(mark)
        return None

    @memoize
    def sentence(self) -> Optional[Any]:
        # sentence: &'if' if_sentence | &'while' while_sentence | call | function | var_def | return_sentence | assign_sentence
        mark = self._mark()
        if (
            self.positive_lookahead(self.expect, 'if')
            and
            (if_sentence := self.if_sentence())
        ):
            return if_sentence
        self._reset(mark)
        if (
            self.positive_lookahead(self.expect, 'while')
            and
            (while_sentence := self.while_sentence())
        ):
            return while_sentence
        self._reset(mark)
        if (
            (call := self.call())
        ):
            return call
        self._reset(mark)
        if (
            (function := self.function())
        ):
            return function
        self._reset(mark)
        if (
            (var_def := self.var_def())
        ):
            return var_def
        self._reset(mark)
        if (
            (return_sentence := self.return_sentence())
        ):
            return return_sentence
        self._reset(mark)
        if (
            (assign_sentence := self.assign_sentence())
        ):
            return assign_sentence
        self._reset(mark)
        return None

    @memoize
    def return_sentence(self) -> Optional[Any]:
        # return_sentence: 'return' expression
        mark = self._mark()
        if (
            (literal := self.expect('return'))
            and
            (a := self.expression())
        ):
            return Return ( value = a )
        self._reset(mark)
        return None

    @memoize
    def function(self) -> Optional[Any]:
        # function: type NAME '(' arg_exp_list? ')' ':' body | type NAME '(' arg_exp_list? ')'
        mark = self._mark()
        if (
            (a := self.type())
            and
            (b := self.name())
            and
            (literal := self.expect('('))
            and
            (c := self.arg_exp_list(),)
            and
            (literal_1 := self.expect(')'))
            and
            (literal_2 := self.expect(':'))
            and
            (d := self.body())
        ):
            return Function ( type = a , name = b . string , args = c if c else [] , body = d )
        self._reset(mark)
        if (
            (a := self.type())
            and
            (b := self.name())
            and
            (literal := self.expect('('))
            and
            (c := self.arg_exp_list(),)
            and
            (literal_1 := self.expect(')'))
        ):
            return Function ( type = a , name = b . string , args = c if c else [] )
        self._reset(mark)
        return None

    @memoize
    def if_sentence(self) -> Optional[Any]:
        # if_sentence: 'if' expression ':' body elif_sentence+?
        mark = self._mark()
        if (
            (literal := self.expect('if'))
            and
            (a := self.expression())
            and
            (literal_1 := self.expect(':'))
            and
            (b := self.body())
            and
            (c := self._loop1_2(),)
        ):
            return If ( exp = a , body = b , elses = c if c else [] )
        self._reset(mark)
        return None

    @memoize
    def elif_sentence(self) -> Optional[Any]:
        # elif_sentence: 'elif' expression ':' body elif_sentence? | else_sentence
        mark = self._mark()
        if (
            (literal := self.expect('elif'))
            and
            (a := self.expression())
            and
            (literal_1 := self.expect(':'))
            and
            (b := self.body())
            and
            (c := self.elif_sentence(),)
        ):
            return If ( exp = a , body = b , elses = c if c else [] )
        self._reset(mark)
        if (
            (else_sentence := self.else_sentence())
        ):
            return else_sentence
        self._reset(mark)
        return None

    @memoize
    def else_sentence(self) -> Optional[Any]:
        # else_sentence: 'else' ':' body
        mark = self._mark()
        if (
            (literal := self.expect('else'))
            and
            (literal_1 := self.expect(':'))
            and
            (body := self.body())
        ):
            return [literal, literal_1, body]
        self._reset(mark)
        return None

    @memoize
    def while_sentence(self) -> Optional[Any]:
        # while_sentence: 'while' expression ':' body
        mark = self._mark()
        if (
            (literal := self.expect('while'))
            and
            (a := self.expression())
            and
            (literal_1 := self.expect(':'))
            and
            (b := self.body())
        ):
            return While ( exp = a , body = b )
        self._reset(mark)
        return None

    @memoize
    def assign_sentence(self) -> Optional[Any]:
        # assign_sentence: expression '=' expression
        mark = self._mark()
        if (
            (a := self.expression())
            and
            (literal := self.expect('='))
            and
            (b := self.expression())
        ):
            return Assign ( targets = [a] , value = b )
        self._reset(mark)
        return None

    @memoize
    def var_def(self) -> Optional[Any]:
        # var_def: type ((NAME ['=' expression] ','?))+
        mark = self._mark()
        if (
            (a := self.type())
            and
            (b := self._loop1_3())
        ):
            return VarDef ( type = a , ** get_var_defs ( b ) )
        self._reset(mark)
        return None

    @memoize
    def arg_def(self) -> Optional[Any]:
        # arg_def: type NAME
        mark = self._mark()
        if (
            (a := self.type())
            and
            (b := self.name())
        ):
            return ArgDef ( type = a , name = b . string )
        self._reset(mark)
        return None

    @memoize
    def basic_type(self) -> Optional[Any]:
        # basic_type: 'int' | 'char' | 'float'
        mark = self._mark()
        if (
            (literal := self.expect('int'))
        ):
            return IntType ( )
        self._reset(mark)
        if (
            (literal := self.expect('char'))
        ):
            return CharType ( )
        self._reset(mark)
        if (
            (literal := self.expect('float'))
        ):
            return FloatType ( )
        self._reset(mark)
        return None

    @memoize
    def pointer_type(self) -> Optional[Any]:
        # pointer_type: basic_type '*'+
        mark = self._mark()
        if (
            (a := self.basic_type())
            and
            (_loop1_4 := self._loop1_4())
        ):
            return Pointer ( type = a )
        self._reset(mark)
        return None

    @memoize
    def var_type(self) -> Optional[Any]:
        # var_type: pointer_type | basic_type
        mark = self._mark()
        if (
            (pointer_type := self.pointer_type())
        ):
            return pointer_type
        self._reset(mark)
        if (
            (basic_type := self.basic_type())
        ):
            return basic_type
        self._reset(mark)
        return None

    @memoize
    def array_type(self) -> Optional[Any]:
        # array_type: var_type (('[' NUMBER ']'))+
        mark = self._mark()
        if (
            (a := self.var_type())
            and
            (b := self._loop1_5())
        ):
            return Array ( type = a , level = [i . string for _ , i , __ in b] )
        self._reset(mark)
        return None

    @memoize
    def type(self) -> Optional[Any]:
        # type: array_type | var_type
        mark = self._mark()
        if (
            (array_type := self.array_type())
        ):
            return array_type
        self._reset(mark)
        if (
            (var_type := self.var_type())
        ):
            return var_type
        self._reset(mark)
        return None

    @memoize
    def expression(self) -> Optional[Any]:
        # expression: arg_def | or_exp
        mark = self._mark()
        if (
            (arg_def := self.arg_def())
        ):
            return arg_def
        self._reset(mark)
        if (
            (or_exp := self.or_exp())
        ):
            return or_exp
        self._reset(mark)
        return None

    @memoize
    def or_exp(self) -> Optional[Any]:
        # or_exp: and_exp (('or' and_exp))+ | and_exp
        mark = self._mark()
        if (
            (a := self.and_exp())
            and
            (b := self._loop1_6())
        ):
            return BoolOp ( op = Or ( ) , values = [a] + [i [1] for i in b] )
        self._reset(mark)
        if (
            (and_exp := self.and_exp())
        ):
            return and_exp
        self._reset(mark)
        return None

    @memoize
    def and_exp(self) -> Optional[Any]:
        # and_exp: bitor_exp (('and' bitor_exp))+ | bitor_exp
        mark = self._mark()
        if (
            (a := self.bitor_exp())
            and
            (b := self._loop1_7())
        ):
            return BoolOp ( op = And ( ) , values = [a] + [i [1] for i in b] )
        self._reset(mark)
        if (
            (bitor_exp := self.bitor_exp())
        ):
            return bitor_exp
        self._reset(mark)
        return None

    @memoize_left_rec
    def bitor_exp(self) -> Optional[Any]:
        # bitor_exp: bitor_exp '|' bitxor_exp | bitxor_exp
        mark = self._mark()
        if (
            (a := self.bitor_exp())
            and
            (literal := self.expect('|'))
            and
            (b := self.bitxor_exp())
        ):
            return BinOp ( left = a , op = BitOr ( ) , right = b )
        self._reset(mark)
        if (
            (bitxor_exp := self.bitxor_exp())
        ):
            return bitxor_exp
        self._reset(mark)
        return None

    @memoize_left_rec
    def bitxor_exp(self) -> Optional[Any]:
        # bitxor_exp: bitxor_exp '^' bitand_exp | bitand_exp
        mark = self._mark()
        if (
            (a := self.bitxor_exp())
            and
            (literal := self.expect('^'))
            and
            (b := self.bitand_exp())
        ):
            return BinOp ( left = a , op = BitXor ( ) , right = b )
        self._reset(mark)
        if (
            (bitand_exp := self.bitand_exp())
        ):
            return bitand_exp
        self._reset(mark)
        return None

    @memoize_left_rec
    def bitand_exp(self) -> Optional[Any]:
        # bitand_exp: bitand_exp '&' compare_exp | compare_exp
        mark = self._mark()
        if (
            (a := self.bitand_exp())
            and
            (literal := self.expect('&'))
            and
            (b := self.compare_exp())
        ):
            return BinOp ( left = a , op = BitAnd ( ) , right = b )
        self._reset(mark)
        if (
            (compare_exp := self.compare_exp())
        ):
            return compare_exp
        self._reset(mark)
        return None

    @memoize
    def compare_exp(self) -> Optional[Any]:
        # compare_exp: shift_exp compares | shift_exp
        mark = self._mark()
        if (
            (a := self.shift_exp())
            and
            (b := self.compares())
        ):
            return Compare ( left = a , ops = [i for i , j in b] , comparators = [j for i , j in b] )
        self._reset(mark)
        if (
            (shift_exp := self.shift_exp())
        ):
            return shift_exp
        self._reset(mark)
        return None

    @memoize
    def compares(self) -> Optional[Any]:
        # compares: compare+
        mark = self._mark()
        if (
            (_loop1_8 := self._loop1_8())
        ):
            return _loop1_8
        self._reset(mark)
        return None

    @memoize
    def compare(self) -> Optional[Any]:
        # compare: '<' shift_exp | '<=' shift_exp | '>' shift_exp | '>=' shift_exp | '==' shift_exp | '!=' shift_exp
        mark = self._mark()
        if (
            (literal := self.expect('<'))
            and
            (a := self.shift_exp())
        ):
            return ( Lt ( ) , a )
        self._reset(mark)
        if (
            (literal := self.expect('<='))
            and
            (a := self.shift_exp())
        ):
            return ( Leq ( ) , a )
        self._reset(mark)
        if (
            (literal := self.expect('>'))
            and
            (a := self.shift_exp())
        ):
            return ( Gt ( ) , a )
        self._reset(mark)
        if (
            (literal := self.expect('>='))
            and
            (a := self.shift_exp())
        ):
            return ( Geq ( ) , a )
        self._reset(mark)
        if (
            (literal := self.expect('=='))
            and
            (a := self.shift_exp())
        ):
            return ( Eq ( ) , a )
        self._reset(mark)
        if (
            (literal := self.expect('!='))
            and
            (a := self.shift_exp())
        ):
            return ( Neq ( ) , a )
        self._reset(mark)
        return None

    @memoize_left_rec
    def shift_exp(self) -> Optional[Any]:
        # shift_exp: shift_exp '<<' add_exp | shift_exp '>>' add_exp | add_exp
        mark = self._mark()
        if (
            (a := self.shift_exp())
            and
            (literal := self.expect('<<'))
            and
            (b := self.add_exp())
        ):
            return BinOp ( left = a , op = RShift ( ) , right = b )
        self._reset(mark)
        if (
            (a := self.shift_exp())
            and
            (literal := self.expect('>>'))
            and
            (b := self.add_exp())
        ):
            return BinOp ( left = a , op = LShift ( ) , right = b )
        self._reset(mark)
        if (
            (add_exp := self.add_exp())
        ):
            return add_exp
        self._reset(mark)
        return None

    @memoize_left_rec
    def add_exp(self) -> Optional[Any]:
        # add_exp: add_exp '+' mul_exp | add_exp '-' mul_exp | mul_exp
        mark = self._mark()
        if (
            (a := self.add_exp())
            and
            (literal := self.expect('+'))
            and
            (b := self.mul_exp())
        ):
            return BinOp ( left = a , op = Add ( ) , right = b )
        self._reset(mark)
        if (
            (a := self.add_exp())
            and
            (literal := self.expect('-'))
            and
            (b := self.mul_exp())
        ):
            return BinOp ( left = a , op = Sub ( ) , right = b )
        self._reset(mark)
        if (
            (mul_exp := self.mul_exp())
        ):
            return mul_exp
        self._reset(mark)
        return None

    @memoize_left_rec
    def mul_exp(self) -> Optional[Any]:
        # mul_exp: mul_exp '*' postfix_exp | mul_exp '/' postfix_exp | mul_exp '%' postfix_exp | postfix_exp
        mark = self._mark()
        if (
            (a := self.mul_exp())
            and
            (literal := self.expect('*'))
            and
            (b := self.postfix_exp())
        ):
            return BinOp ( left = a , op = Mul ( ) , right = b )
        self._reset(mark)
        if (
            (a := self.mul_exp())
            and
            (literal := self.expect('/'))
            and
            (b := self.postfix_exp())
        ):
            return BinOp ( left = a , op = Div ( ) , right = b )
        self._reset(mark)
        if (
            (a := self.mul_exp())
            and
            (literal := self.expect('%'))
            and
            (b := self.postfix_exp())
        ):
            return BinOp ( left = a , op = Mod ( ) , right = b )
        self._reset(mark)
        if (
            (postfix_exp := self.postfix_exp())
        ):
            return postfix_exp
        self._reset(mark)
        return None

    @memoize_left_rec
    def postfix_exp(self) -> Optional[Any]:
        # postfix_exp: postfix_exp '[' expression ']' | call | postfix_exp '.' NAME | primary_exp
        mark = self._mark()
        if (
            (a := self.postfix_exp())
            and
            (literal := self.expect('['))
            and
            (b := self.expression())
            and
            (literal_1 := self.expect(']'))
        ):
            return Subscript ( value = a , slice = b , mode = Load ( ) )
        self._reset(mark)
        if (
            (call := self.call())
        ):
            return call
        self._reset(mark)
        if (
            (postfix_exp := self.postfix_exp())
            and
            (literal := self.expect('.'))
            and
            (name := self.name())
        ):
            return Attribute ( value = a , attr = b . string , mode = Load ( ) )
        self._reset(mark)
        if (
            (primary_exp := self.primary_exp())
        ):
            return primary_exp
        self._reset(mark)
        return None

    @memoize
    def call(self) -> Optional[Any]:
        # call: NAME '(' arg_exp_list? ')'
        mark = self._mark()
        if (
            (a := self.name())
            and
            (literal := self.expect('('))
            and
            (b := self.arg_exp_list(),)
            and
            (literal_1 := self.expect(')'))
        ):
            return Call ( func = a . string , args = b if b else [] )
        self._reset(mark)
        return None

    @memoize
    def arg_exp_list(self) -> Optional[Any]:
        # arg_exp_list: [expression ((',' expression))*]
        # nullable=True
        mark = self._mark()
        if (
            (a := self._tmp_9(),)
        ):
            return get_args ( a )
        self._reset(mark)
        return None

    @memoize
    def primary_exp(self) -> Optional[Any]:
        # primary_exp: NAME | STRING | NUMBER | '(' expression ')'
        mark = self._mark()
        if (
            (name := self.name())
        ):
            return Name ( id = name . string , mode = Load ( ) )
        self._reset(mark)
        if (
            (string := self.string())
        ):
            return String ( value = string . string )
        self._reset(mark)
        if (
            (number := self.number())
        ):
            return Num ( value = number . string )
        self._reset(mark)
        if (
            (literal := self.expect('('))
            and
            (a := self.expression())
            and
            (literal_1 := self.expect(')'))
        ):
            return a
        self._reset(mark)
        return None

    @memoize
    def _loop0_1(self) -> Optional[Any]:
        # _loop0_1: sentences
        mark = self._mark()
        children = []
        while (
            (sentences := self.sentences())
        ):
            children.append(sentences)
            mark = self._mark()
        self._reset(mark)
        return children

    @memoize
    def _loop1_2(self) -> Optional[Any]:
        # _loop1_2: elif_sentence
        mark = self._mark()
        children = []
        while (
            (elif_sentence := self.elif_sentence())
        ):
            children.append(elif_sentence)
            mark = self._mark()
        self._reset(mark)
        return children

    @memoize
    def _loop1_3(self) -> Optional[Any]:
        # _loop1_3: (NAME ['=' expression] ','?)
        mark = self._mark()
        children = []
        while (
            (_tmp_10 := self._tmp_10())
        ):
            children.append(_tmp_10)
            mark = self._mark()
        self._reset(mark)
        return children

    @memoize
    def _loop1_4(self) -> Optional[Any]:
        # _loop1_4: '*'
        mark = self._mark()
        children = []
        while (
            (literal := self.expect('*'))
        ):
            children.append(literal)
            mark = self._mark()
        self._reset(mark)
        return children

    @memoize
    def _loop1_5(self) -> Optional[Any]:
        # _loop1_5: ('[' NUMBER ']')
        mark = self._mark()
        children = []
        while (
            (_tmp_11 := self._tmp_11())
        ):
            children.append(_tmp_11)
            mark = self._mark()
        self._reset(mark)
        return children

    @memoize
    def _loop1_6(self) -> Optional[Any]:
        # _loop1_6: ('or' and_exp)
        mark = self._mark()
        children = []
        while (
            (_tmp_12 := self._tmp_12())
        ):
            children.append(_tmp_12)
            mark = self._mark()
        self._reset(mark)
        return children

    @memoize
    def _loop1_7(self) -> Optional[Any]:
        # _loop1_7: ('and' bitor_exp)
        mark = self._mark()
        children = []
        while (
            (_tmp_13 := self._tmp_13())
        ):
            children.append(_tmp_13)
            mark = self._mark()
        self._reset(mark)
        return children

    @memoize
    def _loop1_8(self) -> Optional[Any]:
        # _loop1_8: compare
        mark = self._mark()
        children = []
        while (
            (compare := self.compare())
        ):
            children.append(compare)
            mark = self._mark()
        self._reset(mark)
        return children

    @memoize
    def _tmp_9(self) -> Optional[Any]:
        # _tmp_9: expression ((',' expression))*
        mark = self._mark()
        if (
            (expression := self.expression())
            and
            (_loop0_14 := self._loop0_14(),)
        ):
            return [expression, _loop0_14]
        self._reset(mark)
        return None

    @memoize
    def _tmp_10(self) -> Optional[Any]:
        # _tmp_10: NAME ['=' expression] ','?
        mark = self._mark()
        if (
            (name := self.name())
            and
            (opt := self._tmp_15(),)
            and
            (opt_1 := self.expect(','),)
        ):
            return [name, opt, opt_1]
        self._reset(mark)
        return None

    @memoize
    def _tmp_11(self) -> Optional[Any]:
        # _tmp_11: '[' NUMBER ']'
        mark = self._mark()
        if (
            (literal := self.expect('['))
            and
            (number := self.number())
            and
            (literal_1 := self.expect(']'))
        ):
            return [literal, number, literal_1]
        self._reset(mark)
        return None

    @memoize
    def _tmp_12(self) -> Optional[Any]:
        # _tmp_12: 'or' and_exp
        mark = self._mark()
        if (
            (literal := self.expect('or'))
            and
            (and_exp := self.and_exp())
        ):
            return [literal, and_exp]
        self._reset(mark)
        return None

    @memoize
    def _tmp_13(self) -> Optional[Any]:
        # _tmp_13: 'and' bitor_exp
        mark = self._mark()
        if (
            (literal := self.expect('and'))
            and
            (bitor_exp := self.bitor_exp())
        ):
            return [literal, bitor_exp]
        self._reset(mark)
        return None

    @memoize
    def _loop0_14(self) -> Optional[Any]:
        # _loop0_14: (',' expression)
        mark = self._mark()
        children = []
        while (
            (_tmp_16 := self._tmp_16())
        ):
            children.append(_tmp_16)
            mark = self._mark()
        self._reset(mark)
        return children

    @memoize
    def _tmp_15(self) -> Optional[Any]:
        # _tmp_15: '=' expression
        mark = self._mark()
        if (
            (literal := self.expect('='))
            and
            (expression := self.expression())
        ):
            return [literal, expression]
        self._reset(mark)
        return None

    @memoize
    def _tmp_16(self) -> Optional[Any]:
        # _tmp_16: ',' expression
        mark = self._mark()
        if (
            (literal := self.expect(','))
            and
            (expression := self.expression())
        ):
            return [literal, expression]
        self._reset(mark)
        return None

    KEYWORDS = ('char', 'int', 'and', 'if', 'return', 'float', 'else', 'elif', 'or', 'while')
    SOFT_KEYWORDS = ()


if __name__ == '__main__':
    from pegen.parser import simple_parser_main
    simple_parser_main(GeneratedParser)
