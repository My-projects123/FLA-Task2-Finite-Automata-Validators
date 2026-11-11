"""Command-line demo for Task 2 validators."""

from __future__ import annotations

import argparse
import sys

from .validators import (
    EMAIL_DFA,
    EMAIL_NFA,
    LIMITATIONS,
    PASSWORD_DFA,
    PASSWORD_PRODUCT,
    PIN_DFA,
    PIN46_DFA,
    PW_PARTS,
    SESSION_DFA,
    STRONG_PIN_DFA,
)

APPS = {
    "pin": PIN_DFA,
    "pin46": PIN46_DFA,
    "session": SESSION_DFA,
    "password": PASSWORD_DFA,
    "email": EMAIL_DFA,
}


SAMPLES = {
    "pin": {
        "accept": ["4821", "0000", "9375", "1234", "0042"],
        "reject": ["482", "48211", "48a1", "12 34", "", "-123"],
    },
    "session": {
        "accept": ["C", "WC", "WWC", "CW", "WWCWW"],
        "reject": ["", "W", "WW", "WWW", "WWWC", "WWWWC"],
    },
    "password": {
        "accept": [
            "Deepak@15",
            "Srm#Aiml9",
            "Trichy1!",
            "P@ssw0rdX",
            "Q1w2e3r4!",
            "Zz9_Zz9_Zz",
        ],
        "reject": [
            "deepak@15",
            "DEEPAK@15",
            "DeepakSrm",
            "Deepak15",
            "Dp@1",
            "Deep ak@15",
            "Abcdefgh1!xyzAB",
        ],
    },
    "email": {
        "accept": [
            "deepak.vf@srmist.edu.in",
            "ra2411026050015@srmist.edu.in",
            "student_15@gmail.com",
            "a-b.c@my-site.co",
            "x@y.io",
        ],
        "reject": [
            "deepak@srmist",
            ".deepak@gmail.com",
            "deepak..vf@gmail.com",
            "deepak@-srm.in",
            "deepak@srm.c0m",
            "deepak@@gmail.com",
        ],
    },
}


def _print_table(app: str, machine) -> None:
    print(f"\n=== {machine.name} ===")
    data = SAMPLES[app]
    print("Accepted:")
    for s in data["accept"]:
        ok, _ = machine.run(s)
        mark = "ACCEPT" if ok else "FAIL*"
        print(f"  [{mark}] {s!r}")
    print("Rejected:")
    for s in data["reject"]:
        ok, _ = machine.run(s)
        mark = "REJECT" if not ok else "FAIL*"
        print(f"  [{mark}] {s!r}")


def _trace(machine, text: str) -> None:
    ok, trace = machine.run(text)
    print(f"\n{machine.name}")
    print(f"input: {text!r}")
    print(f"{'state':<8} {'char':<6} {'sym':<6} {'next':<8}")
    for st, ch, sym, nxt in trace:
        print(f"{st:<8} {ch!r:<6} {sym:<6} {nxt:<8}")
    print("RESULT:", "ACCEPT" if ok else "REJECT")


def _stats() -> None:
    print("Design comparison")
    print(f"  PIN DFA states:              {len(PIN_DFA.reachable())}")
    print(f"  PIN 4-or-6 DFA states:       {len(PIN46_DFA.reachable())}")
    print(f"  Strong-PIN minimal states:   {len(STRONG_PIN_DFA.reachable())}")
    print(f"  Session DFA states:          {len(SESSION_DFA.reachable())}")
    side = sum(len(p.reachable()) for p in PW_PARTS)
    print(f"  Password 5 DFAs side-by-side:{side}")
    print(f"  Password product reachable:  {len(PASSWORD_PRODUCT.reachable())}")
    print(f"  Password minimal:            {len(PASSWORD_DFA.reachable())}")
    raw = EMAIL_NFA.to_dfa()
    print(f"  E-mail NFA states:           {len(EMAIL_NFA.states)}")
    print(f"  E-mail subset DFA:           {len(raw.reachable())}")
    print(f"  E-mail minimal DFA:          {len(EMAIL_DFA.reachable())}")


def _limits() -> None:
    for key, lines in LIMITATIONS.items():
        print(f"\n{key}:")
        for line in lines:
            print(f"  - {line}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="FLA Task 2 validators demo")
    parser.add_argument("app", nargs="?", choices=list(APPS) + ["all"], default="all")
    parser.add_argument("text", nargs="?", help="string to trace")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--limits", action="store_true")
    args = parser.parse_args(argv)

    if args.stats:
        _stats()
        return 0
    if args.limits:
        _limits()
        return 0

    if args.app == "all" and args.text is None:
        for app in ("pin", "session", "password", "email"):
            _print_table(app, APPS[app])
        return 0

    if args.app == "all":
        print("Pick a concrete app when tracing a string.", file=sys.stderr)
        return 2

    machine = APPS[args.app]
    if args.text is None:
        _print_table(args.app if args.app != "pin46" else "pin", machine)
        return 0
    _trace(machine, args.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
