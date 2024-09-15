import sys

sys.path.append("../..")

import pytest
from Basic import TokenKind, FileReader, Error
from Lex import Preprocessor


def examplestest(examples, handle=None):
    for example in examples:
        print(example["filename"], "=" * 64)
        reader = FileReader(example["filename"])
        lexer = Preprocessor(reader)
        if handle != None:
            lexer = handle(lexer)
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


def test_stringconcat():
    examples = [
        {
            "filename": "stringchar.txt",
            "tokens": [
                {
                    "kind": TokenKind.STRINGLITERAL,
                    "text": '1abab1我的世界Minecraft\123"fdas\xabc\n\t\f',
                    "size": 4,
                },
                {"kind": TokenKind.END},
            ],
        }
    ]
    examplestest(examples)


def test_comment():
    def donot_ignore_comment(pp):
        pp.state = []
        return pp

    examples = [
        {
            "filename": "comment.txt",
            "tokens": [
                {"kind": TokenKind.STRINGLITERAL, "text": "a//b"},
                {"kind": TokenKind.COMMENT, "text": " */ //"},
                {"kind": TokenKind.COMMENT, "text": "i();"},
                {"kind": TokenKind.COMMENT, "text": " j();"},
                {"kind": TokenKind.COMMENT, "text": "//"},
                {"kind": TokenKind.IDENTIFIER, "text": "l"},
                {"kind": TokenKind.END},
            ],
        }
    ]
    examplestest(examples, donot_ignore_comment)


def test_define():
    examples = [
        {
            "filename": "define1.txt",
            "tokens": [
                {"kind": TokenKind.INTCONST, "text": "42"},
                {"kind": TokenKind.END},
            ],
        },
        {
            "filename": "define2.txt",
            "tokens": [
                {"kind": TokenKind.IDENTIFIER, "text": "f"},
                {"kind": TokenKind.L_PAREN},
                {"kind": TokenKind.INTCONST, "text": "0"},
                {"kind": TokenKind.COMMA},
                {"kind": TokenKind.IDENTIFIER, "text": "a"},
                {"kind": TokenKind.COMMA},
                {"kind": TokenKind.IDENTIFIER, "text": "b"},
                {"kind": TokenKind.COMMA},
                {"kind": TokenKind.IDENTIFIER, "text": "c"},
                {"kind": TokenKind.R_PAREN},
                {"kind": TokenKind.IDENTIFIER, "text": "f"},
                {"kind": TokenKind.L_PAREN},
                {"kind": TokenKind.INTCONST, "text": "0"},
                {"kind": TokenKind.R_PAREN},
                {"kind": TokenKind.IDENTIFIER, "text": "f"},
                {"kind": TokenKind.L_PAREN},
                {"kind": TokenKind.INTCONST, "text": "0"},
                {"kind": TokenKind.R_PAREN},
                {"kind": TokenKind.IDENTIFIER, "text": "f"},
                {"kind": TokenKind.L_PAREN},
                {"kind": TokenKind.INTCONST, "text": "0"},
                {"kind": TokenKind.COMMA},
                {"kind": TokenKind.IDENTIFIER, "text": "a"},
                {"kind": TokenKind.COMMA},
                {"kind": TokenKind.IDENTIFIER, "text": "b"},
                {"kind": TokenKind.COMMA},
                {"kind": TokenKind.IDENTIFIER, "text": "c"},
                {"kind": TokenKind.R_PAREN},
                {"kind": TokenKind.IDENTIFIER, "text": "f"},
                {"kind": TokenKind.L_PAREN},
                {"kind": TokenKind.INTCONST, "text": "0"},
                {"kind": TokenKind.COMMA},
                {"kind": TokenKind.IDENTIFIER, "text": "a"},
                {"kind": TokenKind.R_PAREN},
                {"kind": TokenKind.IDENTIFIER, "text": "f"},
                {"kind": TokenKind.L_PAREN},
                {"kind": TokenKind.INTCONST, "text": "0"},
                {"kind": TokenKind.COMMA},
                {"kind": TokenKind.IDENTIFIER, "text": "a"},
                {"kind": TokenKind.R_PAREN},
                {"kind": TokenKind.IDENTIFIER, "text": "S"},
                {"kind": TokenKind.IDENTIFIER, "text": "foo"},
                {"kind": TokenKind.IDENTIFIER, "text": "S"},
                {"kind": TokenKind.IDENTIFIER, "text": "bar"},
                {"kind": TokenKind.EQUAL},
                {"kind": TokenKind.L_BRACE},
                {"kind": TokenKind.INTCONST, "text": "1"},
                {"kind": TokenKind.COMMA},
                {"kind": TokenKind.INTCONST, "text": "2"},
                {"kind": TokenKind.R_BRACE},
                {"kind": TokenKind.IDENTIFIER, "text": "ab"},
                {"kind": TokenKind.COMMA},
                {"kind": TokenKind.IDENTIFIER, "text": "c"},
                {"kind": TokenKind.COMMA},
                {"kind": TokenKind.IDENTIFIER, "text": "d"},
                {"kind": TokenKind.STRINGLITERAL, "text": ""},
                {"kind": TokenKind.IDENTIFIER, "text": "a"},
                {"kind": TokenKind.IDENTIFIER, "text": "b"},
                {"kind": TokenKind.IDENTIFIER, "text": "ab"},
                {"kind": TokenKind.END},
            ],
        },
        {
            "filename": "define3.txt",
            "tokens": [
                {"kind": TokenKind.STRINGLITERAL, "text": "x ## y"},
                {"kind": TokenKind.END},
            ],
        },
    ]
    examplestest(examples)


def test_defineerror():
    examples = [
        {"filename": f"defineerror{i}.txt", "expected_exception": [Error], "tokens": []}
        for i in range(1, 13)
    ]
    examplestest(examples)


def test_undef():
    examples = [
        {
            "filename": "undef.txt",
            "tokens": [
                {"kind": TokenKind.INTCONST, "text": "3"},
                {"kind": TokenKind.IDENTIFIER, "text": "A"},
                {"kind": TokenKind.END},
            ],
        }
    ]
    examplestest(examples)


def test_conditional():
    examples = [
        {
            "filename": "conditional.txt",
            "tokens": [
                {"kind": TokenKind.INTCONST, "text": "3"},
                {"kind": TokenKind.INTCONST, "text": "4"},
                {"kind": TokenKind.END},
            ],
        }
    ]
    examplestest(examples)
