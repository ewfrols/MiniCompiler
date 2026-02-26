import sys
from pathlib import Path
from lexer.cli import main

valid_dir = Path("tests/lexer/valid")
expected_dir = Path("tests/lexer/expected")
expected_dir.mkdir(exist_ok=True)

for src_file in valid_dir.glob("*.src"):
    expected_file = expected_dir / src_file.with_suffix(".expected").name
    sys.argv = ["lexer.cli", "--input", str(src_file), "--output", str(expected_file)]
    main()
    print(f"Generated {expected_file}")