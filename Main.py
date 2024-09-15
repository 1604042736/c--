from argparse import ArgumentParser
from Basic import TokenKind, Error, FileReader
from Lex import Preprocessor

version = "1.0.0"


def main():
    argparser = ArgumentParser(description=f"c--编译器 {version}")
    argparser.add_argument("file", help="源代码文件")
    argparser.add_argument(
        "-dump-tokens", help="输出tokens", action="store_true", default=False
    )
    args = argparser.parse_args()
    try:
        reader = FileReader(args.file)
        lexer = Preprocessor(reader)

        token = lexer.next()
        while token.kind != TokenKind.END:
            token = lexer.next()

        if args.dump_tokens:
            for token in lexer.tokens:
                print(token)
    except Error as e:
        e.dump()


if __name__ == "__main__":
    main()
