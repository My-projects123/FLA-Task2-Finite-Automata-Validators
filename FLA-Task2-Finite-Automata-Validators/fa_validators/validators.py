"""
Three real-time validation applications modelled as finite automata.

1. ATM PIN length / format and three-strike card lock
2. Password policy via product of small DFAs
3. E-mail format via NFA → DFA → minimisation

Automata check syntax only. Matching a stored PIN, DNS lookup, or a
compromised-password list are outside the model (see LIMITATIONS).
"""

from __future__ import annotations

import string
from typing import List

from .automata import DEAD, DFA, NFA

# ---------------------------------------------------------------------------
# 1. ATM PIN
# ---------------------------------------------------------------------------
# Σ = {D, O}. L_PIN = { w ∈ D* : |w| = 4 }


def pin_class(ch: str) -> str:
    return "D" if ch in string.digits else "O"


PIN_DFA = DFA(
    name="ATM PIN (exactly 4 digits)",
    alphabet=["D", "O"],
    delta={
        ("q0", "D"): "q1",
        ("q1", "D"): "q2",
        ("q2", "D"): "q3",
        ("q3", "D"): "q4",
    },
    start="q0",
    accepting={"q4"},
    classify=pin_class,
    labels={
        "q0": "0 digits",
        "q1": "1 digit",
        "q2": "2 digits",
        "q3": "3 digits",
        "q4": "4 digits (accept)",
        DEAD: "invalid",
    },
)

PIN46_DFA = DFA(
    name="ATM PIN (4 or 6 digits)",
    alphabet=["D", "O"],
    delta={
        ("q0", "D"): "q1",
        ("q1", "D"): "q2",
        ("q2", "D"): "q3",
        ("q3", "D"): "q4",
        ("q4", "D"): "q5",
        ("q5", "D"): "q6",
    },
    start="q0",
    accepting={"q4", "q6"},
    classify=pin_class,
)


def _identical_digits_dfa() -> DFA:
    digits = list(string.digits)
    delta = {}
    for d in digits:
        delta[("s", d)] = f"{d}1"
        for k in (1, 2, 3):
            delta[(f"{d}{k}", d)] = f"{d}{k + 1}"
    return DFA(
        "four identical digits",
        digits,
        delta,
        "s",
        {f"{d}4" for d in digits},
        classify=lambda c: c,
    )


def _raw_four_digit_dfa() -> DFA:
    digits = list(string.digits)
    delta = {}
    for k in range(4):
        for d in digits:
            delta[(f"p{k}", d)] = f"p{k + 1}"
    return DFA(
        "exactly 4 raw digits",
        digits,
        delta,
        "p0",
        {"p4"},
        classify=lambda c: c,
    )


WEAK_PIN = _identical_digits_dfa()
STRONG_PIN_DFA = (
    _raw_four_digit_dfa()
    .intersect(WEAK_PIN.complement(), "4-digit PIN, digits not all equal")
    .minimize()
)

# Session events: C = correct PIN, W = wrong PIN. Lock after 3 consecutive W.
SESSION_DFA = DFA(
    name="ATM session lock (3 wrong attempts)",
    alphabet=["C", "W"],
    delta={
        ("s0", "C"): "AUTH",
        ("s0", "W"): "s1",
        ("s1", "C"): "AUTH",
        ("s1", "W"): "s2",
        ("s2", "C"): "AUTH",
        ("s2", "W"): "LOCK",
        ("AUTH", "C"): "AUTH",
        ("AUTH", "W"): "AUTH",
        ("LOCK", "C"): "LOCK",
        ("LOCK", "W"): "LOCK",
    },
    start="s0",
    accepting={"AUTH"},
    classify=lambda c: c,
    labels={
        "s0": "0 wrong",
        "s1": "1 wrong",
        "s2": "2 wrong",
        "AUTH": "authenticated",
        "LOCK": "card locked",
    },
)

# ---------------------------------------------------------------------------
# 2. Password policy
# ---------------------------------------------------------------------------
# Length 8..14, ≥1 upper, ≥1 lower, ≥1 digit, ≥1 special. No spaces/other.
SPECIALS = "!@#$%^&*()-_=+[]{};:,.?/"
PW_MIN, PW_MAX = 8, 14


def pw_class(ch: str) -> str:
    if ch in string.ascii_uppercase:
        return "U"
    if ch in string.ascii_lowercase:
        return "L"
    if ch in string.digits:
        return "D"
    if ch in SPECIALS:
        return "S"
    return "O"


PW_ALPHA = ["U", "L", "D", "S", "O"]


def _contains(sym: str) -> DFA:
    delta = {}
    for a in PW_ALPHA:
        if a == "O":
            continue
        delta[("n", a)] = "y" if a == sym else "n"
        delta[("y", a)] = "y"
    return DFA(f"contains {sym}", PW_ALPHA, delta, "n", {"y"}, pw_class)


def _length_dfa() -> DFA:
    delta = {}
    for k in range(PW_MAX):
        for a in PW_ALPHA:
            if a != "O":
                delta[(f"l{k}", a)] = f"l{k + 1}"
    return DFA(
        f"length {PW_MIN}..{PW_MAX}",
        PW_ALPHA,
        delta,
        "l0",
        {f"l{k}" for k in range(PW_MIN, PW_MAX + 1)},
        pw_class,
    )


PW_PARTS: List[DFA] = [
    _contains("U"),
    _contains("L"),
    _contains("D"),
    _contains("S"),
    _length_dfa(),
]


def _password_product() -> DFA:
    d = PW_PARTS[0]
    for part in PW_PARTS[1:]:
        d = d.intersect(part)
    d.name = "Password policy (product DFA)"
    return d


PASSWORD_PRODUCT = _password_product()
PASSWORD_DFA = PASSWORD_PRODUCT.minimize("Password policy (minimal DFA)")


def _coverage_dfa() -> DFA:
    import itertools

    letters = "ULDS"
    subsets = [
        "".join(c for c in letters if c in combo) or "none"
        for r in range(5)
        for combo in itertools.combinations(letters, r)
    ]
    delta = {}
    for s in subsets:
        have = set() if s == "none" else set(s)
        for a in "ULDS":
            nh = have | {a}
            delta[(s, a)] = "".join(c for c in letters if c in nh)
    return DFA(
        "class coverage {U,L,D,S}",
        PW_ALPHA,
        delta,
        "none",
        {"ULDS"},
        pw_class,
        states=subsets,
    )


PW_COVERAGE = _coverage_dfa()

# ---------------------------------------------------------------------------
# 3. E-mail format (practical subset of RFC 5322)
# ---------------------------------------------------------------------------
# local  = alnum+ ([._-] alnum+)*
# domain = label ("." label)* "." tld
# label  = alnum+ ("-"+ alnum+)*
# tld    = letter{2,}


def email_class(ch: str) -> str:
    if ch in string.ascii_letters:
        return "L"
    if ch in string.digits:
        return "D"
    return {".": "DOT", "-": "HY", "_": "US", "@": "AT"}.get(ch, "O")


EM_ALPHA = ["L", "D", "DOT", "HY", "US", "AT", "O"]


def _build_email_nfa() -> NFA:
    """
    States:
      n0 start of local word
      n1 inside local word
      n2 after separator in local (._-)
      n3 just after @
      n4 inside domain label
      n5 after hyphen inside label
      n6 after a dot in domain (could start TLD)
      n7 first letter of TLD
      n8 TLD length ≥ 2 (accepting)
    """
    A = {"L", "D"}
    delta = {}

    def add(p, syms, q):
        for a in syms:
            delta.setdefault((p, a), set()).add(q)

    add("n0", A, "n1")
    add("n1", A, "n1")
    add("n1", {"DOT", "HY", "US"}, "n2")
    add("n2", A, "n1")
    add("n1", {"AT"}, "n3")
    add("n3", A, "n4")
    add("n4", A, "n4")
    add("n4", {"HY"}, "n5")
    add("n5", {"HY"}, "n5")
    add("n5", A, "n4")
    # After a domain label, a DOT may start another label OR the TLD.
    add("n4", {"DOT"}, "n6")
    add("n6", A, "n4")  # next label
    add("n6", {"L"}, "n7")  # guess: start of TLD
    add("n7", {"L"}, "n8")
    add("n8", {"L"}, "n8")
    # From n8 a further DOT may continue the domain (multi-label) then TLD again
    add("n8", {"DOT"}, "n6")

    return NFA(
        name="E-mail format NFA",
        alphabet=EM_ALPHA,
        delta=delta,
        start="n0",
        accepting={"n8"},
        classify=email_class,
        labels={
            "n0": "local start",
            "n1": "in local",
            "n2": "local sep",
            "n3": "after @",
            "n4": "in label",
            "n5": "label hyphen",
            "n6": "after domain .",
            "n7": "TLD len=1",
            "n8": "TLD ok",
        },
    )


EMAIL_NFA = _build_email_nfa()
EMAIL_RAW_DFA = EMAIL_NFA.to_dfa("E-mail format DFA")
EMAIL_DFA = EMAIL_RAW_DFA.minimize("E-mail format (minimal DFA)")

# ---------------------------------------------------------------------------
# Independent checkers (oracle) used by tests
# ---------------------------------------------------------------------------


def oracle_pin(text: str) -> bool:
    return len(text) == 4 and text.isdigit()


def oracle_session(events: str) -> bool:
    wrong = 0
    auth = False
    locked = False
    for e in events:
        if locked:
            continue
        if e == "C":
            auth = True
            wrong = 0
        elif e == "W":
            wrong += 1
            if wrong >= 3:
                locked = True
                auth = False
    return auth and not locked


def oracle_password(text: str) -> bool:
    if not (PW_MIN <= len(text) <= PW_MAX):
        return False
    has = {"U": False, "L": False, "D": False, "S": False}
    for ch in text:
        c = pw_class(ch)
        if c == "O":
            return False
        has[c] = True
    return all(has.values())


def oracle_email(text: str) -> bool:
    import re

    local = r"[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*"
    label = r"[A-Za-z0-9]+(?:-+[A-Za-z0-9]+)*"
    tld = r"[A-Za-z]{2,}"
    pattern = rf"^{local}@(?:{label}\.)+{tld}$"
    return re.fullmatch(pattern, text) is not None


LIMITATIONS = {
    "pin": [
        "Does not compare the PIN with the bank's stored value (semantics).",
        "Does not model PIN change / expiry.",
        "'Digits not all equal' needs the raw alphabet and grows to dozens of states.",
    ],
    "password": [
        "Does not check against a breached-password list.",
        "Does not enforce keyboard-pattern / username-similarity rules (not regular).",
        "Unicode letters are classified as Other and rejected by design.",
    ],
    "email": [
        "Does not verify that the domain has MX records (DNS).",
        "Full RFC 5322 (quoted local parts, comments) is not modelled.",
        "Nested comments need a stack — not a finite automaton.",
    ],
}
