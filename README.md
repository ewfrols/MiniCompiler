# MiniCompiler – Sprint 1: Лексический анализатор

Учебный проект компилятора для упрощённого C-подобного языка.  
Цель первого спринта: реализовать лексер (токенизатор) с поддержкой комментариев и препроцессора (опционально).

## Структура проекта
├── src/ # Исходный код
│ ├── lexer/ # Лексер
│ └── utils/ # Вспомогательные модули
├── tests/ # Тесты
│ ├── lexer/ # Тесты лексера (valid, invalid, expected)
│ └── test_lexer.py
├── examples/ # Примеры программ
├── docs/ # Документация
├── setup.py # Установка пакета
├── pyproject.toml # Альтернативный конфиг
└── requirements-dev.txt

## Установка и запуск

1. Клонируйте репозиторий.
2. (Рекомендуется) Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
pip install -e .[dev]
minicompiler-lex --input examples/hello.src --output tokens.txt
pytest tests/
