"""
Reusable finite-automata library for the validators.

Validators keep a small alphabet of character classes (D, U, L, …) so diagrams
stay readable. Missing transitions go to an explicit trap state that never
accepts.

Features: DFA run/trace, NFA → DFA subset construction, product (intersection),
complement, Myhill–Nerode minimisation, Graphviz DOT export.
"""

from __future__ import annotations

from collections import deque
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

DEAD = "qD"


def _natural(state) -> Tuple:
    """Sort key that keeps q0, q1, … in order and puts the trap last."""
    s = str(state)
    if s == DEAD:
        return (2, s)
    digits = "".join(ch for ch in s if ch.isdigit())
    if digits:
        return (0, int(digits), s)
    return (1, s)


class DFA:
    def __init__(
        self,
        name: str,
        alphabet: Iterable[str],
        delta: Dict[Tuple[str, str], str],
        start: str,
        accepting: Iterable[str],
        classify: Callable[[str], str],
        states: Optional[Iterable[str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.alphabet = list(alphabet)
        self.start = start
        self.accepting = set(accepting)
        self.classify = classify
        self.labels = labels or {}

        found: Set[str] = {start} | set(self.accepting)
        for (p, _), q in delta.items():
            found.add(p)
            found.add(q)
        self.states = list(states) if states is not None else sorted(found, key=_natural)

        self.delta = dict(delta)
        need_dead = False
        for p in list(self.states):
            for a in self.alphabet:
                if (p, a) not in self.delta:
                    self.delta[(p, a)] = DEAD
                    need_dead = True
        if need_dead or DEAD in self.states:
            if DEAD not in self.states:
                self.states.append(DEAD)
            for a in self.alphabet:
                self.delta[(DEAD, a)] = DEAD

    def step(self, state: str, symbol: str) -> str:
        return self.delta.get((state, symbol), DEAD)

    def run(self, text: str):
        """Return (accepted, trace) where trace entries are (state, char, symbol, next)."""
        state = self.start
        trace = []
        for ch in text:
            sym = self.classify(ch)
            nxt = self.step(state, sym) if sym in self.alphabet else DEAD
            trace.append((state, ch, sym, nxt))
            state = nxt
        return state in self.accepting, trace

    def accepts(self, text: str) -> bool:
        return self.run(text)[0]

    def accepts_symbols(self, symbols: Iterable[str]) -> bool:
        state = self.start
        for s in symbols:
            state = self.step(state, s)
        return state in self.accepting

    def reachable(self) -> Set[str]:
        seen = {self.start}
        todo = deque([self.start])
        while todo:
            p = todo.popleft()
            for a in self.alphabet:
                q = self.step(p, a)
                if q not in seen:
                    seen.add(q)
                    todo.append(q)
        return seen

    def complement(self, name: Optional[str] = None) -> "DFA":
        return DFA(
            name or f"not ({self.name})",
            self.alphabet,
            dict(self.delta),
            self.start,
            set(self.states) - self.accepting,
            self.classify,
            states=self.states,
        )

    def intersect(self, other: "DFA", name: Optional[str] = None) -> "DFA":
        assert self.alphabet == other.alphabet, "alphabets must match"
        start = (self.start, other.start)
        delta = {}
        seen = {start}
        todo = deque([start])
        while todo:
            p, q = todo.popleft()
            for a in self.alphabet:
                nxt = (self.step(p, a), other.step(q, a))
                delta[((p, q), a)] = nxt
                if nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        accepting = {
            s for s in seen if s[0] in self.accepting and s[1] in other.accepting
        }
        names = {s: f"{s[0]}|{s[1]}" for s in seen}
        return DFA(
            name or f"{self.name} ∩ {other.name}",
            self.alphabet,
            {(names[p], a): names[q] for (p, a), q in delta.items()},
            names[start],
            {names[s] for s in accepting},
            self.classify,
            states=sorted(names.values(), key=_natural),
        )

    def minimize(self, name: Optional[str] = None) -> "DFA":
        states = sorted(self.reachable(), key=_natural)
        idx = {s: i for i, s in enumerate(states)}
        n = len(states)
        marked = [[False] * n for _ in range(n)]
        for i in range(n):
            for j in range(i):
                if (states[i] in self.accepting) != (states[j] in self.accepting):
                    marked[i][j] = True

        changed = True
        while changed:
            changed = False
            for i in range(n):
                for j in range(i):
                    if marked[i][j]:
                        continue
                    for a in self.alphabet:
                        x = idx[self.step(states[i], a)]
                        y = idx[self.step(states[j], a)]
                        if x != y and marked[max(x, y)][min(x, y)]:
                            marked[i][j] = True
                            changed = True
                            break

        parent = list(range(n))

        def find(k: int) -> int:
            while parent[k] != k:
                parent[k] = parent[parent[k]]
                k = parent[k]
            return k

        for i in range(n):
            for j in range(i):
                if not marked[i][j]:
                    parent[find(i)] = find(j)

        groups: Dict[int, List[str]] = {}
        for i, s in enumerate(states):
            groups.setdefault(find(i), []).append(s)

        block_of = {s: root for root, members in groups.items() for s in members}
        order: List[int] = []
        seen_blocks: Set[int] = set()
        todo = deque([block_of[self.start]])
        seen_blocks.add(block_of[self.start])
        while todo:
            b = todo.popleft()
            order.append(b)
            rep = groups[b][0]
            for a in self.alphabet:
                nb = block_of[self.step(rep, a)]
                if nb not in seen_blocks:
                    seen_blocks.add(nb)
                    todo.append(nb)

        dead_block = None
        for b in order:
            rep = groups[b][0]
            if rep not in self.accepting and all(
                block_of[self.step(rep, a)] == b for a in self.alphabet
            ):
                dead_block = b
                break

        newname = {}
        k = 0
        for b in order:
            if b == dead_block:
                newname[b] = DEAD
            else:
                newname[b] = f"m{k}"
                k += 1

        delta = {}
        for b in order:
            rep = groups[b][0]
            for a in self.alphabet:
                delta[(newname[b], a)] = newname[block_of[self.step(rep, a)]]
        accepting = {newname[b] for b in order if groups[b][0] in self.accepting}
        return DFA(
            name or f"{self.name} (minimal)",
            self.alphabet,
            delta,
            newname[block_of[self.start]],
            accepting,
            self.classify,
            states=[newname[b] for b in order],
        )

    def to_dot(self, omit_dead: bool = True) -> str:
        lines = [
            f'digraph "{self.name}" {{',
            "  rankdir=LR;",
            '  node [shape=circle, fontname="Helvetica"];',
            '  edge [fontname="Helvetica"];',
            '  start [shape=point];',
            f'  start -> "{self.start}";',
        ]
        visible = [s for s in self.states if not (omit_dead and s == DEAD)]
        for s in visible:
            shape = "doublecircle" if s in self.accepting else "circle"
            label = self.labels.get(s, s)
            lines.append(f'  "{s}" [shape={shape}, label="{label}"];')
        # merge multi-label edges
        buckets: Dict[Tuple[str, str], List[str]] = {}
        for (p, a), q in self.delta.items():
            if omit_dead and (p == DEAD or q == DEAD):
                continue
            if omit_dead and p not in visible:
                continue
            buckets.setdefault((p, q), []).append(a)
        for (p, q), syms in sorted(buckets.items()):
            label = ",".join(sorted(set(syms)))
            lines.append(f'  "{p}" -> "{q}" [label="{label}"];')
        lines.append("}")
        return "\n".join(lines)


class NFA:
    def __init__(
        self,
        name: str,
        alphabet: Iterable[str],
        delta: Dict[Tuple[str, str], Set[str]],
        start: str,
        accepting: Iterable[str],
        classify: Callable[[str], str],
        states: Optional[Iterable[str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.alphabet = list(alphabet)
        self.delta = {k: set(v) for k, v in delta.items()}
        self.start = start
        self.accepting = set(accepting)
        self.classify = classify
        self.labels = labels or {}
        found: Set[str] = {start} | set(self.accepting)
        for (p, _), qs in self.delta.items():
            found.add(p)
            found |= qs
        self.states = list(states) if states is not None else sorted(found, key=_natural)

    def move(self, states: Iterable[str], symbol: str) -> Set[str]:
        out: Set[str] = set()
        for p in states:
            out |= self.delta.get((p, symbol), set())
        return out

    def epsilon_closure(self, states: Iterable[str]) -> Set[str]:
        stack = list(states)
        closure = set(states)
        while stack:
            p = stack.pop()
            for q in self.delta.get((p, "ε"), set()):
                if q not in closure:
                    closure.add(q)
                    stack.append(q)
        return closure

    def accepts(self, text: str) -> bool:
        current = self.epsilon_closure({self.start})
        for ch in text:
            sym = self.classify(ch)
            if sym not in self.alphabet:
                return False
            current = self.epsilon_closure(self.move(current, sym))
            if not current:
                return False
        return bool(current & self.accepting)

    def to_dfa(self, name: Optional[str] = None) -> DFA:
        start_set = frozenset(self.epsilon_closure({self.start}))
        names: Dict[frozenset, str] = {start_set: "n0"}
        order = [start_set]
        todo = deque([start_set])
        delta = {}
        while todo:
            S = todo.popleft()
            for a in self.alphabet:
                T = frozenset(self.epsilon_closure(self.move(S, a)))
                if not T:
                    continue
                if T not in names:
                    names[T] = f"n{len(names)}"
                    order.append(T)
                    todo.append(T)
                delta[(names[S], a)] = names[T]

        accepting = {names[S] for S in order if S & self.accepting}
        # fill missing moves to dead via DFA constructor
        return DFA(
            name or f"{self.name} (DFA)",
            self.alphabet,
            delta,
            names[start_set],
            accepting,
            self.classify,
            states=[names[S] for S in order],
        )

    def to_dot(self) -> str:
        lines = [
            f'digraph "{self.name}" {{',
            "  rankdir=LR;",
            '  node [shape=circle, fontname="Helvetica"];',
            '  start [shape=point];',
            f'  start -> "{self.start}";',
        ]
        for s in self.states:
            shape = "doublecircle" if s in self.accepting else "circle"
            label = self.labels.get(s, s)
            lines.append(f'  "{s}" [shape={shape}, label="{label}"];')
        buckets: Dict[Tuple[str, str], List[str]] = {}
        for (p, a), qs in self.delta.items():
            for q in qs:
                buckets.setdefault((p, q), []).append(a)
        for (p, q), syms in sorted(buckets.items()):
            label = ",".join(sorted(set(syms)))
            lines.append(f'  "{p}" -> "{q}" [label="{label}"];')
        lines.append("}")
        return "\n".join(lines)
