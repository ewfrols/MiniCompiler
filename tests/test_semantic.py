import pytest
from pathlib import Path
from lexer import Scanner, TokenType
from miniparser import Parser
from semantic import SemanticAnalyzer

BASE_DIR    = Path(__file__).parent
VALID_DIR   = BASE_DIR / "semantic" / "valid"
INVALID_DIR = BASE_DIR / "semantic" / "invalid"


def analyse_source(source: str):
    scanner = Scanner(source)
    tokens = []
    while True:
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type == TokenType.END_OF_FILE:
            break
    parser = Parser(tokens)
    tree = parser.parse()
    assert not parser.errors, f"Unexpected parse errors: {parser.errors}"
    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(tree)
    return errors, analyzer


@pytest.mark.parametrize("src_file", sorted(VALID_DIR.glob("*.src")))
def test_valid_semantic(src_file):
    source = src_file.read_text(encoding="utf-8")
    errors, _ = analyse_source(source)
    assert not errors, (
        f"Unexpected semantic errors in {src_file.name}:\n"
        + "\n".join(str(e) for e in errors)
    )


@pytest.mark.parametrize("src_file", sorted(INVALID_DIR.glob("*.src")))
def test_invalid_semantic(src_file):
    source = src_file.read_text(encoding="utf-8")
    errors, _ = analyse_source(source)
    assert len(errors) > 0, (
        f"Expected semantic errors in {src_file.name}, but got none"
    )
