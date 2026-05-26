from setuptools import setup, find_packages

setup(
    name="minicompiler",
    version="0.1.0",
    packages=find_packages("src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "minicompiler-lex = lexer.cli:main",
            "minicompiler-parse = miniparser.cli:main",
            "minicompiler-check = semantic.cli:main",
            "minicompiler-ir = ir.cli:main",
        ],
    },
    install_requires=[],
    extras_require={
        "dev": ["pytest"],
    },
)