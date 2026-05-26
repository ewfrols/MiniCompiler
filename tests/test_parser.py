import pytest
from pathlib import Path
from lexer import Scanner, TokenType
from miniparser import Parser, ParseError
from miniparser.printer import TextPrinter

BASE_DIR = Path(__file__).parent
VALID_DIR = BASE_DIR / "parser" / "valid"
INVALID_DIR = BASE_DIR / "parser" / "invalid"
EXPECTED_DIR = BASE_DIR / "parser" / "expected"


def parse_source(source: str):
    scanner = Scanner(source)
    tokens = []
    while True:
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type == TokenType.END_OF_FILE:
            break
    parser = Parser(tokens)
    tree = parser.parse()
    return tree, parser.errors


@pytest.mark.parametrize("src_file", sorted(VALID_DIR.glob("*.src")))
def test_valid_parser(src_file):
    source = src_file.read_text(encoding="utf-8")
    tree, errors = parse_source(source)

    assert not errors, f"Unexpected parse errors in {src_file.name}: {errors}"

    expected_file = EXPECTED_DIR / src_file.with_suffix(".ast").name
    if expected_file.exists():
        expected = expected_file.read_text(encoding="utf-8").strip()
        actual = TextPrinter().render(tree).strip()
        assert actual == expected, (
            f"AST mismatch for {src_file.name}\n"
            f"--- expected ---\n{expected}\n"
            f"--- actual ---\n{actual}"
        )
    else:
        pytest.fail(f"Expected file {expected_file} not found")


@pytest.mark.parametrize("src_file", sorted(INVALID_DIR.glob("*.src")))
def test_invalid_parser(src_file):
    source = src_file.read_text(encoding="utf-8")
    _, errors = parse_source(source)
    assert len(errors) > 0, f"Expected parse errors in {src_file.name}, but got none"
