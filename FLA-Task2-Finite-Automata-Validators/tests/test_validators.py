"""Unit + oracle tests for Task 2 validators."""

import itertools
import random
import string

from fa_validators.validators import (
    EMAIL_DFA,
    EMAIL_NFA,
    PASSWORD_DFA,
    PIN_DFA,
    SESSION_DFA,
    STRONG_PIN_DFA,
    oracle_email,
    oracle_password,
    oracle_pin,
    oracle_session,
)


def test_pin_samples():
    for s in ["4821", "0000", "9375", "1234", "0042"]:
        assert PIN_DFA.accepts(s)
        assert oracle_pin(s)
    for s in ["482", "48211", "48a1", "12 34", "", "-123"]:
        assert not PIN_DFA.accepts(s)
        assert not oracle_pin(s)


def test_pin_exhaustive_short():
    # all strings length ≤ 5 over {0-9, a}
    alphabet = list(string.digits) + ["a"]
    for n in range(6):
        for chars in itertools.product(alphabet, repeat=n):
            s = "".join(chars)
            assert PIN_DFA.accepts(s) == oracle_pin(s)


def test_session_samples():
    for s in ["C", "WC", "WWC", "CW", "WWCWW"]:
        assert SESSION_DFA.accepts(s)
        assert oracle_session(s)
    for s in ["", "W", "WW", "WWW", "WWWC", "WWWWC"]:
        assert not SESSION_DFA.accepts(s)
        assert not oracle_session(s)


def test_strong_pin_rejects_identical():
    assert not STRONG_PIN_DFA.accepts("0000")
    assert not STRONG_PIN_DFA.accepts("7777")
    assert STRONG_PIN_DFA.accepts("1234")
    assert STRONG_PIN_DFA.accepts("1121")


def test_password_samples():
    for s in ["Deepak@15", "Srm#Aiml9", "Trichy1!", "P@ssw0rdX", "Q1w2e3r4!"]:
        assert PASSWORD_DFA.accepts(s), s
        assert oracle_password(s), s
    for s in ["deepak@15", "DEEPAK@15", "DeepakSrm", "Dp@1", "Deep ak@15"]:
        assert not PASSWORD_DFA.accepts(s), s
        assert not oracle_password(s), s


def test_password_random_oracle():
    rng = random.Random(15)
    pool = string.ascii_letters + string.digits + "!@#$%^&*"
    for _ in range(2000):
        n = rng.randint(0, 16)
        s = "".join(rng.choice(pool + " ") for _ in range(n))
        assert PASSWORD_DFA.accepts(s) == oracle_password(s)


def test_email_samples():
    for s in [
        "deepak.vf@srmist.edu.in",
        "ra2411026050015@srmist.edu.in",
        "student_15@gmail.com",
        "a-b.c@my-site.co",
        "x@y.io",
    ]:
        assert EMAIL_NFA.accepts(s), s
        assert EMAIL_DFA.accepts(s), s
        assert oracle_email(s), s
    for s in [
        "deepak@srmist",
        ".deepak@gmail.com",
        "deepak..vf@gmail.com",
        "deepak@-srm.in",
        "deepak@srm.c0m",
        "deepak@@gmail.com",
    ]:
        assert not EMAIL_NFA.accepts(s), s
        assert not EMAIL_DFA.accepts(s), s
        assert not oracle_email(s), s


def test_email_nfa_dfa_agree_random():
    rng = random.Random(15)
    alphabet = list("ab1.-_@")
    for _ in range(3000):
        n = rng.randint(0, 10)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        assert EMAIL_NFA.accepts(s) == EMAIL_DFA.accepts(s) == oracle_email(s)
