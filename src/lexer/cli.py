import sys
import argparse
from pathlib import Path
from .scanner import Scanner

def main():
    parser = argparse.ArgumentParser(description="MiniCompiler Lexer")
    parser.add_argument("--input", "-i", required=True, help="Входной файл с исходным кодом")
    parser.add_argument("--output", "-o", required=True, help="Файл для вывода токенов")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Ошибка: файл {args.input} не найден", file=sys.stderr)
        sys.exit(1)

    scanner = Scanner(source)
    with open(args.output, "w", encoding="utf-8") as out:
        while True:
            tok = scanner.next_token()
            out.write(str(tok) + "\n")
            if tok.type.name == "END_OF_FILE":
                break

    if scanner.errors:
        print(f"Лексических ошибок: {len(scanner.errors)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()