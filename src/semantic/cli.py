import sys
import argparse
from pathlib import Path
from lexer.scanner import Scanner
from lexer.token import TokenType
from miniparser.parser import Parser
from .analyzer import SemanticAnalyzer


def main():
    ap = argparse.ArgumentParser(description="MiniCompiler Semantic Checker")
    ap.add_argument("--input", "-i", required=True, help="Входной файл с исходным кодом")
    ap.add_argument("--output", "-o", default=None, help="Файл для вывода таблицы символов")
    ap.add_argument("--show-types", action="store_true", help="Показать типы выражений")
    args = ap.parse_args()

    try:
        source = Path(args.input).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Ошибка: файл {args.input} не найден", file=sys.stderr)
        sys.exit(1)

    # Lex
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

    # Parse
    parser = Parser(tokens)
    tree = parser.parse()
    if parser.errors:
        print(f"Синтаксических ошибок: {len(parser.errors)}", file=sys.stderr)
        sys.exit(1)

    # Semantic analysis
    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(tree)

    # Symbol table dump
    dump = analyzer.get_symbol_table().dump()
    if args.output:
        Path(args.output).write_text(dump, encoding="utf-8")
    else:
        print(dump)

    if args.show_types:
        print("\nТипы выражений:")
        for node_id, t in analyzer.get_type_map().items():
            print(f"  node#{node_id}: {t}")

    if errors:
        print(f"\nСемантических ошибок: {len(errors)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
