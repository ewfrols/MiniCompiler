# MiniCompiler

Учебный проект: компилятор для упрощённого C-подобного языка на Python.

## Структура проекта

```
MiniCompiler/
├── src/
│   ├── lexer/          # Спринт 1: лексер (токенизатор)
│   └── miniparser/     # Спринт 2: рекурсивный спуск, AST, printer
├── tests/
│   ├── lexer/          # valid / invalid / expected для лексера
│   ├── parser/         # valid / invalid / expected для парсера
│   ├── test_lexer.py
│   └── test_parser.py
├── docs/
│   └── grammar.ebnf    # EBNF-грамматика языка
├── examples/           # Примеры .src файлов
├── setup.py
└── requirements-dev.txt
```

## Установка

```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac
pip install -e .[dev]
```

## Использование

### Лексер

```bash
minicompiler-lex --input examples/hello.src --output tokens.txt
```

### Парсер

```bash
# Текстовый AST (по умолчанию)
minicompiler-parse --input examples/hello.src --output tree.ast

# Graphviz DOT
minicompiler-parse --input examples/hello.src --output tree.dot --ast-format dot
```

## Тесты

```bash
pytest tests/
```

## Грамматика (краткая)

```ebnf
program     = { declaration } EOF ;
declaration = fn_decl | struct_decl | var_decl | statement ;
fn_decl     = "fn" IDENTIFIER "(" [params] ")" [":" type] block ;
var_decl    = type IDENTIFIER ["=" expression] ";" ;
statement   = block | if_stmt | while_stmt | for_stmt | return_stmt | expr_stmt ;
```

Полная грамматика с приоритетами операторов: [docs/grammar.ebnf](docs/grammar.ebnf)
