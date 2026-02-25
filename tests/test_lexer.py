import pytest
from pathlib import Path
from lexer import Scanner, TokenType

# Пути к тестовым директориям
BASE_DIR = Path(__file__).parent
VALID_DIR = BASE_DIR / "lexer" / "valid"
INVALID_DIR = BASE_DIR / "lexer" / "invalid"
EXPECTED_DIR = BASE_DIR / "lexer" / "expected"

def scan_all_tokens(source: str):
    """Сканирует весь исходный код и возвращает список токенов и ошибок."""
    scanner = Scanner(source)
    tokens = []
    while True:
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type == TokenType.END_OF_FILE:
            break
    return tokens, scanner.errors

def token_to_expected_string(tok):
    """Преобразует токен в формат, используемый в .expected файлах."""
    base = f"{tok.line}:{tok.column} {tok.type.name} \"{tok.lexeme}\""
    if tok.literal is not None:
        base += f" {tok.literal}"
    return base

@pytest.mark.parametrize("src_file", VALID_DIR.glob("*.src"))
def test_valid_lexer(src_file):
    with open(src_file, "r", encoding="utf-8") as f:
        source = f.read()
    tokens, errors = scan_all_tokens(source)

    # Проверяем, что нет ошибок
    assert not errors, f"Unexpected errors in {src_file.name}: {errors}"

    # Сравниваем с ожидаемым файлом
    expected_file = EXPECTED_DIR / src_file.with_suffix(".expected").name
    if expected_file.exists():
        with open(expected_file, "r", encoding="utf-8") as ef:
            expected_lines = [line.strip() for line in ef if line.strip()]
        actual_lines = [token_to_expected_string(t) for t in tokens]
        assert actual_lines == expected_lines, f"Mismatch in {src_file.name}"
    else:
        pytest.fail(f"Expected file {expected_file} not found")

@pytest.mark.parametrize("src_file", INVALID_DIR.glob("*.src"))
def test_invalid_lexer(src_file):
    with open(src_file, "r", encoding="utf-8") as f:
        source = f.read()
    _, errors = scan_all_tokens(source)
    assert len(errors) > 0, f"Expected errors in {src_file.name}, but got none"