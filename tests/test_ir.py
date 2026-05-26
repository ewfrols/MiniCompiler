import pytest
from pathlib import Path
from lexer import Scanner, TokenType
from miniparser import Parser
from semantic import SemanticAnalyzer
from ir import IRGenerator, IRTextPrinter, IRDotPrinter

BASE_DIR  = Path(__file__).parent
VALID_DIR = BASE_DIR / "ir" / "valid"


def build_ir(source: str):
    """Полный конвейер: исходник -> IR."""
    scanner = Scanner(source)
    tokens = []
    while True:
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type == TokenType.END_OF_FILE:
            break
    assert not scanner.errors, f"Лексических ошибок: {scanner.errors}"

    parser = Parser(tokens)
    tree = parser.parse()
    assert not parser.errors, f"Синтаксических ошибок: {parser.errors}"

    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(tree)
    assert not errors, f"Семантических ошибок: {errors}"

    gen = IRGenerator()
    program = gen.generate(tree)
    return program


@pytest.mark.parametrize("src_file", sorted(VALID_DIR.glob("*.src")))
def test_ir_generates(src_file):
    """IR генерируется без ошибок для всех валидных файлов."""
    source = src_file.read_text(encoding="utf-8")
    program = build_ir(source)
    assert len(program.functions) > 0, f"Нет функций в IR для {src_file.name}"


@pytest.mark.parametrize("src_file", sorted(VALID_DIR.glob("*.src")))
def test_ir_text_printer(src_file):
    """Текстовый принтер не падает и возвращает непустую строку."""
    source = src_file.read_text(encoding="utf-8")
    program = build_ir(source)
    text = IRTextPrinter().render(program)
    assert text.strip(), f"Пустой вывод IRTextPrinter для {src_file.name}"
    assert "function" in text, "Вывод должен содержать объявление функции"


@pytest.mark.parametrize("src_file", sorted(VALID_DIR.glob("*.src")))
def test_ir_dot_printer(src_file):
    """DOT-принтер не падает и возвращает корректный Graphviz-заголовок."""
    source = src_file.read_text(encoding="utf-8")
    program = build_ir(source)
    dot = IRDotPrinter().render(program)
    assert dot.startswith("digraph CFG"), f"DOT-вывод должен начинаться с 'digraph CFG'"


def test_blocks_terminated():
    """Каждый базовый блок должен заканчиваться инструкцией перехода или возврата."""
    from ir.instructions import Opcode
    source = (VALID_DIR / "test_if_stmt.src").read_text(encoding="utf-8")
    program = build_ir(source)
    term_ops = {Opcode.JUMP, Opcode.JUMP_IF, Opcode.JUMP_IF_NOT, Opcode.RETURN}
    for fn in program.functions:
        for block in fn.blocks:
            if block.instructions:
                last = block.instructions[-1].opcode
                assert last in term_ops, (
                    f"Блок '{block.label}' в функции '{fn.name}' "
                    f"не завершён инструкцией перехода/возврата (последняя: {last})"
                )


def test_cfg_edges_resolved():
    """После генерации рёбра CFG (successors) должны быть заполнены."""
    source = (VALID_DIR / "test_while_loop.src").read_text(encoding="utf-8")
    program = build_ir(source)
    fn = program.functions[0]
    total_edges = sum(len(b.successors) for b in fn.blocks)
    assert total_edges > 0, "В функции с циклом должны быть рёбра CFG"


def test_fn_call_ir():
    """В IR для вызова функции присутствует инструкция CALL."""
    from ir.instructions import Opcode
    source = (VALID_DIR / "test_fn_call.src").read_text(encoding="utf-8")
    program = build_ir(source)
    all_ops = [
        instr.opcode
        for fn in program.functions
        for block in fn.blocks
        for instr in block.instructions
    ]
    assert Opcode.CALL in all_ops, "Ожидается инструкция CALL в IR"
