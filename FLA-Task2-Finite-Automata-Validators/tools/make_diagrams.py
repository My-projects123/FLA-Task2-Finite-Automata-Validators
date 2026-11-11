#!/usr/bin/env python3
"""Write Graphviz DOT files (and PNG/SVG if `dot` is installed)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fa_validators.validators import (  # noqa: E402
    EMAIL_DFA,
    EMAIL_NFA,
    PIN_DFA,
    PIN46_DFA,
    PW_COVERAGE,
    PW_PARTS,
    SESSION_DFA,
)

OUT = ROOT / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def write(name: str, dot: str) -> None:
    path = OUT / f"{name}.dot"
    path.write_text(dot)
    print("wrote", path)
    if shutil.which("dot"):
        for fmt in ("png", "svg"):
            dest = OUT / f"{name}.{fmt}"
            subprocess.run(["dot", f"-T{fmt}", "-o", str(dest), str(path)], check=True)
            print("wrote", dest)


def main() -> None:
    write("pin_dfa", PIN_DFA.to_dot())
    write("pin46_dfa", PIN46_DFA.to_dot())
    write("session_dfa", SESSION_DFA.to_dot())
    write("password_has_upper", PW_PARTS[0].to_dot())
    write("password_length", PW_PARTS[4].to_dot())
    write("password_coverage", PW_COVERAGE.to_dot())
    write("email_nfa", EMAIL_NFA.to_dot())
    write("email_dfa", EMAIL_DFA.to_dot())


if __name__ == "__main__":
    main()
