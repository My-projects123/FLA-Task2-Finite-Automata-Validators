#!/usr/bin/env python3
"""Export automata JSON + rebuild docs/index.html live demo."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fa_validators.validators import (  # noqa: E402
    EMAIL_DFA,
    PASSWORD_DFA,
    PIN_DFA,
    SESSION_DFA,
)

OUT_JSON = ROOT / "docs" / "automata.json"
OUT_HTML = ROOT / "docs" / "index.html"

EXAMPLES = {
    "pin": {
        "accept": ["4821", "0000", "9375", "1234", "0042"],
        "reject": ["482", "48211", "48a1", "12 34", "", "-123"],
    },
    "session": {
        "accept": ["C", "WC", "WWC", "CW", "WWCWW"],
        "reject": ["", "W", "WW", "WWW", "WWWC", "WWWWC"],
    },
    "password": {
        "accept": ["Deepak@15", "Srm#Aiml9", "Trichy1!", "P@ssw0rdX", "Q1w2e3r4!"],
        "reject": ["deepak@15", "DEEPAK@15", "DeepakSrm", "Dp@1", "Deep ak@15"],
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


def dump_dfa(dfa, title: str, key: str, omit_dead: bool = True):
    delta = {}
    for (p, a), q in dfa.delta.items():
        if omit_dead and (p == "qD" or q == "qD") and key != "session":
            # keep dead transitions for correctness in the runner
            pass
        delta[f"{p}|{a}"] = q
    live = sorted(dfa.reachable() - ({"qD"} if omit_dead else set()), key=str)
    return {
        "title": title,
        "name": dfa.name,
        "start": dfa.start,
        "accepting": sorted(dfa.accepting),
        "alphabet": list(dfa.alphabet),
        "delta": delta,
        "examples": EXAMPLES[key],
        "states": len(live),
        "state_list": live,
    }


def pin_svg() -> str:
    xs = [70, 150, 230, 310, 390]
    names = ["q0", "q1", "q2", "q3", "q4"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 90" width="100%" height="90">',
        '<circle cx="18" cy="45" r="3" fill="#111"/>',
        f'<line x1="21" y1="45" x2="{xs[0]-22}" y2="45" stroke="#111" marker-end="url(#arrow)"/>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">'
        '<path d="M0,0 L6,3 L0,6 Z" fill="#111"/></marker></defs>',
    ]
    for i, (x, n) in enumerate(zip(xs, names)):
        stroke = "#111"
        parts.append(f'<g class="node" data-state="{n}">')
        parts.append(f'<circle class="ring" cx="{x}" cy="45" r="20" fill="#fff" stroke="{stroke}" stroke-width="2"/>')
        if n == "q4":
            parts.append(f'<circle cx="{x}" cy="45" r="16" fill="none" stroke="{stroke}" stroke-width="2"/>')
        parts.append(f'<text x="{x}" y="49" text-anchor="middle" font-family="Helvetica" font-size="13">{n}</text></g>')
        if i < 4:
            parts.append(
                f'<line x1="{x+22}" y1="45" x2="{xs[i+1]-22}" y2="45" stroke="#111" marker-end="url(#arrow)"/>'
            )
            mid = (x + xs[i + 1]) / 2
            parts.append(f'<text x="{mid}" y="38" text-anchor="middle" font-size="11">D</text>')
    parts.append("</svg>")
    return "".join(parts)


def session_svg() -> str:
    # s0 -> s1 -> s2 -> LOCK ; C arrows to AUTH
    return """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 180" width="100%" height="180">
  <defs><marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#111"/></marker></defs>
  <g class="node" data-state="s0"><circle class="ring" cx="60" cy="110" r="22" fill="#fff" stroke="#111" stroke-width="2"/><text x="60" y="114" text-anchor="middle" font-size="13">s0</text></g>
  <g class="node" data-state="s1"><circle class="ring" cx="170" cy="110" r="22" fill="#fff" stroke="#111" stroke-width="2"/><text x="170" y="114" text-anchor="middle" font-size="13">s1</text></g>
  <g class="node" data-state="s2"><circle class="ring" cx="280" cy="110" r="22" fill="#fff" stroke="#111" stroke-width="2"/><text x="280" y="114" text-anchor="middle" font-size="13">s2</text></g>
  <g class="node" data-state="LOCK"><circle class="ring" cx="400" cy="110" r="26" fill="#fff" stroke="#c53030" stroke-width="2"/><text x="400" y="114" text-anchor="middle" font-size="12">LOCK</text></g>
  <g class="node" data-state="AUTH"><circle class="ring" cx="280" cy="40" r="26" fill="#fff" stroke="#276749" stroke-width="2"/><circle cx="280" cy="40" r="20" fill="none" stroke="#276749" stroke-width="2"/><text x="280" y="44" text-anchor="middle" font-size="12">AUTH</text></g>
  <line x1="82" y1="110" x2="148" y2="110" stroke="#111" marker-end="url(#a2)"/><text x="115" y="102" text-anchor="middle" font-size="11">W</text>
  <line x1="192" y1="110" x2="258" y2="110" stroke="#111" marker-end="url(#a2)"/><text x="225" y="102" text-anchor="middle" font-size="11">W</text>
  <line x1="302" y1="110" x2="374" y2="110" stroke="#111" marker-end="url(#a2)"/><text x="338" y="102" text-anchor="middle" font-size="11">W</text>
  <path d="M60,88 C60,50 200,20 254,30" fill="none" stroke="#111" marker-end="url(#a2)"/><text x="140" y="42" font-size="11">C</text>
  <path d="M170,88 C190,60 230,45 254,40" fill="none" stroke="#111" marker-end="url(#a2)"/><text x="210" y="58" font-size="11">C</text>
  <path d="M290,88 C300,70 295,55 290,50" fill="none" stroke="#111" marker-end="url(#a2)"/><text x="308" y="70" font-size="11">C</text>
</svg>
"""


def email_svg() -> str:
    # Simplified readable chain for the minimal email DFA states
    states = EMAIL_DFA.state_list if hasattr(EMAIL_DFA, "state_list") else sorted(
        EMAIL_DFA.reachable() - {"qD"}, key=str
    )
    # Use actual start/accept from machine
    start = EMAIL_DFA.start
    acc = sorted(EMAIL_DFA.accepting)
    # Draw as a horizontal row of live states (excluding trap)
    live = [s for s in sorted(EMAIL_DFA.reachable(), key=str) if s != "qD"]
    w = max(520, 70 * len(live) + 40)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 100" width="100%" height="100">',
        '<defs><marker id="ae" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#111"/></marker></defs>',
    ]
    xs = [50 + i * 70 for i in range(len(live))]
    for x, n in zip(xs, live):
        parts.append(f'<g class="node" data-state="{n}">')
        parts.append(f'<circle class="ring" cx="{x}" cy="50" r="20" fill="#fff" stroke="#111" stroke-width="2"/>')
        if n in EMAIL_DFA.accepting:
            parts.append(f'<circle cx="{x}" cy="50" r="15" fill="none" stroke="#111" stroke-width="2"/>')
        parts.append(f'<text x="{x}" y="54" text-anchor="middle" font-size="12">{n}</text></g>')
    parts.append(
        f'<text x="{w/2}" y="90" text-anchor="middle" font-size="11" fill="#4a5568">'
        f"start={start}; accepting={','.join(acc)} — highlight follows the live run</text>"
    )
    parts.append("</svg>")
    return "".join(parts)


HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>FA Validators — live demo</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
 body{font-family:Segoe UI,Helvetica,Arial,sans-serif;margin:0;background:#f6f7f9;color:#1d2330}
 header{background:#1f3b63;color:#fff;padding:14px 24px}
 header h1{margin:0;font-size:20px} header p{margin:4px 0 0;font-size:13px;opacity:.85}
 main{display:grid;grid-template-columns:minmax(300px,380px) 1fr;gap:18px;padding:18px 24px}
 @media(max-width:900px){main{grid-template-columns:1fr}}
 .card{background:#fff;border:1px solid #dde1e7;border-radius:8px;padding:14px}
 label{font-size:13px;font-weight:600;display:block;margin:8px 0 4px}
 select,input{width:100%;box-sizing:border-box;padding:8px;font-size:15px;border:1px solid #bfc6d1;border-radius:6px;font-family:Consolas,monospace}
 .verdict{margin-top:12px;padding:10px;border-radius:6px;font-weight:700;text-align:center;font-size:16px}
 .ok{background:#e3f4e7;color:#16692c}.bad{background:#fbe5e5;color:#9b1c1c}
 table{border-collapse:collapse;width:100%;font-size:13px;font-family:Consolas,monospace}
 td,th{border-bottom:1px solid #eceff3;padding:4px 6px;text-align:left}
 .chips span{display:inline-block;margin:3px;padding:3px 8px;border-radius:12px;font-size:12px;cursor:pointer;font-family:Consolas,monospace}
 .a{background:#e3f4e7}.r{background:#fbe5e5}
 #diagram .node.cur .ring{fill:#ffd54f!important}
 #diagram .node.visited .ring{fill:#e8f0fe!important}
 small{color:#5b6473}
</style></head><body>
<header><h1>Finite-automata validators — live demo</h1>
<p>21CSC301T Formal Language and Automata · CLA-2 Task 2 · Deepak V. F. (RA2411026050015)</p></header>
<main>
<div class="card">
 <label>Application</label><select id="app"></select>
 <label>Input string</label><input id="inp" autocomplete="off" spellcheck="false">
 <div id="verdict" class="verdict"></div>
 <label>Examples (click to try)</label><div class="chips" id="chips"></div>
 <p><small id="info"></small></p>
</div>
<div class="card">
 <div id="diagram"></div>
 <table><thead><tr><th>#</th><th>state</th><th>char</th><th>class</th><th>next</th></tr></thead><tbody id="trace"></tbody></table>
</div>
</main>
<script>
const A = __AUTOMATA__;
const SVG = __SVG__;
const CLASSIFY = {
 pin: c => /[0-9]/.test(c) ? "D" : "O",
 session: c => c,
 password: c => /[A-Z]/.test(c)?"U":/[a-z]/.test(c)?"L":/[0-9]/.test(c)?"D":"!@#$%^&*()-_=+[]{};:,.?/".includes(c)?"S":"O",
 email: c => /[A-Za-z]/.test(c)?"L":/[0-9]/.test(c)?"D":({".":"DOT","-":"HY","_":"US","@":"AT"}[c]||"O")
};
const sel = document.getElementById("app"), inp = document.getElementById("inp");
for (const k of Object.keys(A)) sel.add(new Option(A[k].title, k));
function run(){
 const k = sel.value, d = A[k], s = inp.value;
 let st = d.start; const rows = [], visited = new Set([st]);
 [...s].forEach((ch,i)=>{const sym = CLASSIFY[k](ch);
   const nx = d.alphabet.includes(sym) ? (d.delta[st+"|"+sym]||"qD") : "qD";
   rows.push(`<tr><td>${i+1}</td><td>${st}</td><td>${ch===" "?"␣":escapeHtml(ch)}</td><td>${sym}</td><td>${nx}</td></tr>`);
   st = nx; visited.add(st);});
 const ok = d.accepting.includes(st);
 const v = document.getElementById("verdict");
 v.className = "verdict " + (ok?"ok":"bad");
 v.textContent = (ok?"ACCEPTED":"REJECTED") + " — final state " + st;
 document.getElementById("trace").innerHTML = rows.join("") || "<tr><td colspan=5><em>empty input</em></td></tr>";
 const dg = document.getElementById("diagram");
 dg.querySelectorAll("g.node").forEach(g=>{
   const t=g.getAttribute("data-state");
   g.classList.toggle("cur", t===st);
   g.classList.toggle("visited", visited.has(t)&&t!==st);
 });
}
function escapeHtml(s){return s.replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));}
function load(){
 const k = sel.value, d = A[k];
 if (SVG[k]) document.getElementById("diagram").innerHTML = SVG[k];
 else document.getElementById("diagram").innerHTML =
   `<p><small>Password minimal DFA has ${d.states} states — too dense to draw. The transition table still updates live. Coverage of {U,L,D,S} + length is what the product encodes.</small></p>`;
 document.getElementById("chips").innerHTML =
   d.examples.accept.map(x=>`<span class="a">${x===""?"(empty)":escapeHtml(x)}</span>`).join("") +
   d.examples.reject.map(x=>`<span class="r">${x===""?"(empty)":escapeHtml(x)}</span>`).join("");
 document.querySelectorAll("#chips span").forEach(sp=>sp.onclick=()=>{inp.value = sp.textContent==="(empty)"?"":sp.textContent; run();});
 document.getElementById("info").textContent = d.name + " — " + d.states + " live states; alphabet {" + d.alphabet.join(", ") + "}";
 inp.value = d.examples.accept[0] || "";
 run();
}
sel.onchange = load; inp.oninput = run;
load();
</script></body></html>
"""


def main() -> None:
    data = {
        "pin": dump_dfa(PIN_DFA, "ATM PIN verification", "pin"),
        "session": dump_dfa(SESSION_DFA, "ATM session lock-out", "session", omit_dead=False),
        "password": dump_dfa(PASSWORD_DFA, "Password policy", "password"),
        "email": dump_dfa(EMAIL_DFA, "E-mail format", "email"),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, indent=2))
    svg = {
        "pin": pin_svg(),
        "session": session_svg(),
        "email": email_svg(),
    }
    html = (
        HTML.replace("__AUTOMATA__", json.dumps(data))
        .replace("__SVG__", json.dumps(svg))
    )
    OUT_HTML.write_text(html)
    print("wrote", OUT_JSON)
    print("wrote", OUT_HTML)


if __name__ == "__main__":
    main()
