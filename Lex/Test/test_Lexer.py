import sys

sys.path.append("../..")

import pytest

from Basic import TokenKind, Token, FileReader, Error
from Lex import Lexer


def examplestest(examples):
    for example in examples:
        reader = FileReader(example["filename"])
        lexer = Lexer(reader)
        expected_exception = example.get("expected_exception", [])
        if expected_exception:
            with pytest.raises(*expected_exception):
                token = lexer.next()
                while token.kind != TokenKind.END:
                    token = lexer.next()
            continue
        else:
            token = lexer.next()
            while token.kind != TokenKind.END:
                token = lexer.next()
        i = 0
        while i < len(lexer.tokens) and i < len(example["tokens"]):
            token = lexer.tokens[i]
            print(token, example["tokens"][i])
            for attr, val in example["tokens"][i].items():
                assert getattr(token, attr) == val
            i += 1
        assert i == len(lexer.tokens) and i == len(example["tokens"])


def test_emptyfile():
    examples = [{"filename": "emptyfile.txt", "tokens": [{"kind": TokenKind.END}]}]
    examplestest(examples)


def test_punctuator():
    examples = [
        {
            "filename": "punctuator.txt",
            "tokens": [{"kind": kind} for kind in list(Token.punctuator.values())[::-1]]
            + [{"kind": TokenKind.END}],
        }
    ]
    examplestest(examples)


def test_identifier():
    examples = [
        {
            "filename": "identifier.txt",
            "tokens": [
                {"kind": TokenKind.IDENTIFIER, "text": "a"},
                {"kind": TokenKind.IDENTIFIER, "text": "abc"},
                {"kind": TokenKind.IF},
                {"kind": TokenKind.BOOL},
                {"kind": TokenKind.BOOL},
                {"kind": TokenKind.IDENTIFIER, "text": "我的世界"},
                {"kind": TokenKind.END},
            ],
        }
    ]
    examplestest(examples)


def test_stringchar():
    examples = [
        {
            "filename": "stringchar.txt",
            "tokens": [
                {"kind": TokenKind.STRINGLITERAL, "text": "1ab"},
                {"kind": TokenKind.STRINGLITERAL, "text": "ab1"},
                {
                    "kind": TokenKind.STRINGLITERAL,
                    "text": "我的世界",
                    "size": 4,
                },
                {
                    "kind": TokenKind.STRINGLITERAL,
                    "text": "Minecraft",
                    "size": 4,
                },
                {
                    "kind": TokenKind.STRINGLITERAL,
                    "text": '\123"fdas',
                    "size": 4,
                },
                {
                    "kind": TokenKind.STRINGLITERAL,
                    "text": "\xabc\n\t\f",
                    "size": 4,
                },
                {"kind": TokenKind.END},
            ],
        }
    ]
    examplestest(examples)


def test_stringerror():
    examples = [
        {"filename": "stringerror1.txt", "expected_exception": [Error], "tokens": []},
        {"filename": "stringerror2.txt", "expected_exception": [Error], "tokens": []},
    ]
    examplestest(examples)


def test_number():
    examples = [
        {
            "filename": "number.txt",
            "tokens": [
                {"kind": TokenKind.INTCONST, "text": "114"},
                {"kind": TokenKind.INTCONST, "text": "514"},
                {"kind": TokenKind.IDENTIFIER, "text": "b"},
                {"kind": TokenKind.INTCONST, "text": "0x1bf52"},
                {"kind": TokenKind.INTCONST, "text": "0x1bf52u"},
                {"kind": TokenKind.INTCONST, "text": "0x1bf52ul"},
                {"kind": TokenKind.INTCONST, "text": "0x1bf52ull"},
                {"kind": TokenKind.INTCONST, "text": "0337522"},
                {"kind": TokenKind.INTCONST, "text": "0b11011111101010010"},
                {"kind": TokenKind.FLOATCONST, "text": "114514e-4"},
                {"kind": TokenKind.FLOATCONST, "text": "114.514e-1"},
                {"kind": TokenKind.FLOATCONST, "text": "1024e+4"},
                {"kind": TokenKind.FLOATCONST, "text": "10.24"},
                {"kind": TokenKind.FLOATCONST, "text": ".1024"},
                {"kind": TokenKind.END},
            ],
        }
    ]
    examplestest(examples)
