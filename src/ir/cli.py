import sys
import argparse
from pathlib import Path

from lexer.scanner import Scanner
from lexer.token import TokenType
from miniparser.parser import Parser
from semantic.analyzer import SemanticAnalyzer
from .generator import IRGenerator
from .printer import IRTextPrinter, IRDotPrinter


def main():
    ap = argparse.ArgumentParser(description="MiniCompiler IR Generator")
    ap.add_argument("--input",  "-i", required=True, help="Входной файл с исходным кодом")
    ap.add_argument("--output", "-o", default=None,  help="Файл для записи IR (по умолчанию stdout)")
    ap.add_argument(
        "--format", "-f",
        choices=["text", "dot"],
        default="text",
        help="Формат вывода: text (по умолчанию) или dot (Graphviz CFG)",
    )
    ap.add_argument("--stats", action="store_true", help="Показать статистику IR")
    args = ap.parse_args()

    try:
        source = Path(args.input).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Ошибка: файл {args.input} не найден", file=sys.stderr)
        sys.exit(1)

    # лексический анализ
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

    # синтаксический анализ
    parser = Parser(tokens)
    tree = parser.parse()
    if parser.errors:
        print(f"Синтаксических ошибок: {len(parser.errors)}", file=sys.stderr)
        sys.exit(1)

    # семантический анализ
    analyzer = SemanticAnalyzer()
    sem_errors = analyzer.analyze(tree)
    if sem_errors:
        print(f"Семантических ошибок: {len(sem_errors)}", file=sys.stderr)
        sys.exit(1)

    # генерация IR
    gen = IRGenerator()
    program = gen.generate(tree)

    # вывод
    if args.format == "dot":
        output = IRDotPrinter().render(program)
    else:
        output = IRTextPrinter().render(program)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)

    # статистика
    if args.stats:
        total_instrs = sum(
            len(b.instructions)
            for fn in program.functions
            for b in fn.blocks
        )
        total_blocks = sum(len(fn.blocks) for fn in program.functions)
        print(f"\nФункций:      {len(program.functions)}", file=sys.stderr)
        print(f"Базовых блоков: {total_blocks}",           file=sys.stderr)
        print(f"Инструкций:   {total_instrs}",             file=sys.stderr)


if __name__ == "__main__":
    main()
