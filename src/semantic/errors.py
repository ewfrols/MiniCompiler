class SemanticError(Exception):
    def __init__(self, message: str, line: int, column: int, kind: str = "error"):
        self.message = message
        self.line = line
        self.column = column
        self.kind = kind
        super().__init__(f"{line}:{column}: semantic {kind}: {message}")
