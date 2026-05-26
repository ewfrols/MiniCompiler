# MiniCompiler

Учебный проект: компилятор для упрощённого C-подобного языка на Python.

## Структура проекта

```
MiniCompiler/
├── src/
│   ├── lexer/          # Спринт 1: лексер (токенизатор)
│   ├── miniparser/     # Спринт 2: рекурсивный спуск, AST, printer
│   ├── semantic/       # Спринт 3: семантический анализ, таблица символов
│   └── ir/             # Спринт 4: промежуточное представление (IR)
├── tests/
│   ├── lexer/          # valid / invalid / expected для лексера
│   ├── parser/         # valid / invalid / expected для парсера
│   ├── semantic/       # valid / invalid для семантики
│   ├── ir/             # valid для IR
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_semantic.py
│   └── test_ir.py
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

### Семантический анализ

```bash
# Проверка и вывод таблицы символов в stdout
minicompiler-check --input examples/hello.src

# Сохранить таблицу символов в файл
minicompiler-check --input examples/hello.src --output symbols.txt

# Дополнительно показать типы выражений
minicompiler-check --input examples/hello.src --show-types
```

### Генерация IR

```bash
# Текстовый IR (по умолчанию)
minicompiler-ir --input examples/hello.src

# Сохранить IR в файл
minicompiler-ir --input examples/hello.src --output program.ir

# Граф потока управления в Graphviz DOT
minicompiler-ir --input examples/hello.src --format dot --output cfg.dot

# Показать статистику
minicompiler-ir --input examples/hello.src --stats
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
