# Finite Automata for Real-Time Validation

**Course:** 21CSC301T Formal Language and Automata, CLA-2, Assessment Task 2  
**Student:** Deepak V. F. (RA2411026050015), B.Tech AIML 'A', III year  
**Faculty:** Dr. C. Gunasundari, SRM IST Tiruchirappalli

DFAs/NFAs for three everyday input checks:

| # | Application | Automaton | Notes |
|---|---|---|---|
| 1 | ATM PIN verification | 4-digit PIN DFA + 3-strikes session DFA | also 4-or-6 and “not all equal” |
| 2 | Password policy | product of 5 small DFAs, then minimised | length 8–14, U/L/D/S |
| 3 | E-mail address format | NFA → subset construction → minimal DFA | practical RFC 5322 subset |

## Live demo

Open the browser demo (no install needed):

```bash
open docs/index.html
```

Or serve it:

```bash
python3 -m http.server 8765 --directory docs
# then visit http://127.0.0.1:8765
```

Type a PIN / password / e-mail (or click the example chips). The page shows ACCEPT/REJECT, highlights the current state, and prints every transition.

Rebuild the demo from the Python DFAs after you change a machine:

```bash
python3 tools/build_demo.py
```

## Run the CLI and tests

```bash
pip install -r requirements.txt
python3 -m fa_validators.cli                  # accept/reject tables
python3 -m fa_validators.cli email deepak@srm.c0m
python3 -m fa_validators.cli --stats
python3 -m fa_validators.cli --limits
python3 -m pytest -q
python3 tools/make_diagrams.py                # optional; needs Graphviz `dot` for PNG/SVG
```

## Languages (summary)

- **PIN:** Σ = {D, O}, L = { w ∈ D* : |w| = 4 }
- **Password:** Σ = {U, L, D, S, O}, L = L_U ∩ L_L ∩ L_D ∩ L_S ∩ L_len
- **E-mail:** local `alnum+([._-]alnum+)*` `@` domain labels `.` TLD of ≥ 2 letters

Automata check **syntax only**. Stored-PIN match, DNS, and breached-password lists are outside the model.

## Layout

```
fa_validators/   automata library + validators + CLI
tests/           oracle-backed unit tests
docs/index.html  live browser demo
docs/diagrams/   Graphviz DOT sources
tools/           build_demo.py, make_diagrams.py
```
