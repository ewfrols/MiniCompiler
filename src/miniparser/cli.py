import sys
import argparse
from pathlib import Path
from lexer.scanner import Scanner
from lexer.token import TokenType
from .parser import Parser
from .printer import TextPrinter, DotPrinter


def main():
    ap = argparse.ArgumentParser(description="MiniCompiler Parser")
    ap.add_argument("--input", "-i", required=True, help="Входной файл с исходным кодом")
    ap.add_argument("--output", "-o", required=True, help="Файл для вывода AST")
    ap.add_argument(
        "--ast-format", "-f",
        choices=["text", "dot"],
        default="text",
        help="Формат вывода AST: text (по умолчанию) или dot (Graphviz)",
    )
    args = ap.parse_args()

    try:
        source = Path(args.input).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Ошибка: файл {args.input} не найден", file=sys.stderr)
        sys.exit(1)

    scanner = Scanner(source)
    tokens = []
    while True:
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type == TokenType.END_OF_FILE:
            break

    if scanner.errors:
        print(f"Лексических ошибок: {len(scanner.errors)}", file=sys.stderr)
        sys.exit(1)

    parser = Parser(tokens)
    tree = parser.parse()

    if args.ast_format == "dot":
        printer = DotPrinter()
    else:
        printer = TextPrinter()

    output = printer.render(tree)
    Path(args.output).write_text(output, encoding="utf-8")

    if parser.errors:
        print(f"Синтаксических ошибок: {len(parser.errors)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
