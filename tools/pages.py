#!/usr/bin/env python3
"""pages.py — the pages that answer a question rather than describe a record.

  /near/    what is good near me, and what is worth the drive
  /sauce/   the sauce spectrum: how much tomato, sugar, vinegar and mustard, measured
  /quiz/    which side are you on
  /art/     handled by site.py's type index; this module supplies the gallery strip

Imported by site.py. Everything renders at build time; the only client-side work is
the reader's own geolocation and the sorting that follows it.

Chart colours are validated with the dataviz skill's checker against this site's own
surfaces (light #fdfaf3, dark #1f1b18):

  four-class "first on the label" — vinegar #2a78d6, mustard #eda100, other #1baf7a,
  tomato #e34948 (light) / #3987e5 #c98500 #199e70 #e66767 (dark). Both modes pass;
  the CVD warn band obliges secondary encoding, which is here as direct labels, a
  legend, 2px gaps between segments and a table twin under every chart.

  Everything else is one hue (the site's ember) with position carrying the magnitude.
"""
from __future__ import annotations

import html
import json
import math
import re
import statistics

import usmap

def E(x) -> str:
    """html.escape, but a null field is a blank rather than a crash — a JSON field is
    null here when nobody published the thing, which is a state the site prints."""
    return html.escape("" if x is None else str(x))

# base key -> (label, one-line gloss). Order runs hot to sweet, which is how a menu reads.
BASES = [
    ("cayenne-butter", "Cayenne and butter", "aged cayenne pepper sauce loosened with melted butter. Buffalo."),
    ("vinegar-pepper", "Vinegar and pepper", "the bottle itself, before anybody adds fat."),
    ("dry-rub", "Dry rub", "no liquid at all: salt, pepper, paprika, garlic, shaken on hot."),
    ("citrus-pepper", "Citrus and pepper", "lemon pepper, dry or loosened with butter into wet."),
    ("herb-garlic", "Herb and garlic", "garlic, parmesan, butter — the pizzeria's answer."),
    ("mustard", "Mustard", "prepared mustard as the body, not the accent."),
    ("sweet-tomato", "Sweet and red", "tomato, sugar, vinegar, cooked to cling."),
    ("soy-sweet", "Soy and sweet", "soy sauce, sugar, garlic, chile — Korean and Japanese lines."),
    ("chile-crisp", "Chile paste and crisp", "gochujang, sambal, crisp chilli in oil."),
    ("dairy", "Dairy dips", "blue cheese and ranch: the cup beside the basket."),
    ("other", "Other", "everything the map above does not hold."),
]
BASE_LABEL = {k: v for k, v, _ in BASES}

# First-ingredient classes, in stack order. Order is the validated one: the dataviz
# palette checker (scripts/validate_palette.js) passes every adjacent pair against
# this site's own surfaces (#fffdf6 light, #1e1b16 dark). Re-run it before touching
# a colour or a position — red beside green failed at deutan ΔE 6.9.
FIRST_CLASSES = [
    ("pepper", "Pepper or chile first", "#e34948", "#e66767"),
    ("vinegar", "Vinegar or water first", "#2a78d6", "#3987e5"),
    ("fat", "Butter or oil first", "#eda100", "#c98500"),
    ("sugar", "Sugar or tomato first", "#8757c9", "#a07ede"),
    ("other", "Something else first", "#1baf7a", "#199e70"),
]

CHART_CSS = """
.viz{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1rem 1.1rem;margin:1rem 0}
.viz h3{margin:.1rem 0 .2rem;font-size:1.06rem}.viz .note{font-size:.86rem;color:var(--mute);margin:.1rem 0 .7rem}
.viz svg{width:100%;height:auto;display:block;overflow:visible}
.viz .axis{font:500 11.5px -apple-system,"Segoe UI",Roboto,sans-serif;fill:var(--mute)}
.viz .rowlab{font:600 13px -apple-system,"Segoe UI",Roboto,sans-serif;fill:var(--ink)}
.viz .vallab{font:600 11.5px -apple-system,"Segoe UI",Roboto,sans-serif;fill:var(--mute)}
.viz .grid{stroke:var(--line);stroke-width:1}
.viz .dot{fill:var(--sauce);stroke:var(--panel);stroke-width:2}
.viz .med{stroke:var(--ink);stroke-width:2;stroke-linecap:round}
.viz .seg{stroke:var(--panel);stroke-width:2}
.viz figcaption{font-size:.8rem;color:var(--mute);margin-top:.5rem}
.legend-row{display:flex;flex-wrap:wrap;gap:.45rem .9rem;margin:.5rem 0 .2rem;font-size:.84rem;font-family:-apple-system,"Segoe UI",Roboto,sans-serif}
.legend-row span{display:inline-flex;align-items:center;gap:.35rem;color:var(--ink)}
.legend-row i{width:.78rem;height:.78rem;border-radius:3px;display:inline-block}
details.tbl{margin:.6rem 0 0}details.tbl summary{cursor:pointer;font-size:.86rem;color:var(--mute);font-family:-apple-system,"Segoe UI",Roboto,sans-serif}
details.tbl table{font-size:.86rem;margin-top:.5rem}
.smallmult{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:.9rem;margin-top:.7rem}
.smallmult figure{margin:0;background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:.5rem .55rem}
.smallmult figcaption{font-size:.84rem;color:var(--ink);font-weight:600;margin:0 0 .25rem;font-family:-apple-system,"Segoe UI",Roboto,sans-serif}
.smallmult figcaption small{display:block;font-weight:400;color:var(--mute);font-size:.76rem}
"""

NEAR_CSS = """
.finder{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1rem 1.1rem;margin:.8rem 0 1.2rem}
.finder .row{display:flex;gap:.6rem;flex-wrap:wrap;align-items:center}
.finder input[type=search]{flex:1;min-width:12rem;font:inherit;font-size:1.05rem;padding:.55rem .75rem;border:2px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink)}
.chips{display:flex;flex-wrap:wrap;gap:.4rem;margin:.7rem 0 0}
.chips button{font:inherit;font-size:.85rem;font-family:-apple-system,"Segoe UI",Roboto,sans-serif;padding:.3rem .7rem;border-radius:999px;border:1.5px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer}
.chips button[aria-pressed=true]{background:var(--sauce);border-color:var(--sauce);color:#fff}
.hit{display:grid;grid-template-columns:auto 1fr auto;gap:.2rem .8rem;align-items:baseline;padding:.55rem 0;border-bottom:1px solid var(--line)}
.hit .mi{font-variant-numeric:tabular-nums;font-weight:700;color:var(--sauce);white-space:nowrap;font-family:-apple-system,"Segoe UI",Roboto,sans-serif}
.hit .nm{font-weight:600}.hit .wh{grid-column:2;font-size:.86rem;color:var(--mute)}
.hit .wk{grid-column:2;display:flex;align-items:center;gap:.55rem;margin-top:.3rem;font-size:.8rem;color:var(--mute)}
.hit .wk em{font-style:normal;color:var(--sauce);font-weight:600}
.nohours{font-size:.8rem;color:var(--line)}
.daystrip{height:26px;width:176px;display:block;flex:0 0 auto}
.hit .tg{grid-column:2;font-size:.8rem;display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.15rem}
.hit .go{font-size:.82rem;white-space:nowrap}
.drive{display:grid;grid-template-columns:repeat(auto-fill,minmax(16rem,1fr));gap:.9rem}
.drive .card b{display:block;font-size:1.05rem}
.drive .card .why{font-size:.84rem;color:var(--mute);margin-top:.25rem}
.stars{color:var(--gold);letter-spacing:.06em}
"""


def esc_js(obj) -> str:
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


# ---------------------------------------------------------------- near me

def near_page(page, places: dict, recs: list, tagvocab: dict, site_url: str) -> str:
    rows = []
    for p in places["places"]:
        if p.get("lat") is None:
            continue
        rows.append({
            "n": p["name"], "u": p.get("url"), "la": round(p["lat"], 4), "lo": round(p["lon"], 4),
            "c": p.get("city") or "", "co": p.get("county") or "", "s": p.get("state") or "",
            "t": p.get("tags") or [], "a": p.get("recognitions") or 0, "rb": p.get("recognized_by") or [],
            "d": "".join((p.get("days") or {}).get(k, "unknown")[0] for k in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")),
            "so": bool(p.get("sold_out")), "ht": p.get("hours_text") or "",
            "b": (p.get("blurb") or "")[:150], "w": p.get("website") or "", "h": p.get("hours") or "",
            "st": p.get("styles") or [], "sc": p.get("status") or "",
        })
    towns: dict = {}
    for r in rows:
        if r["c"]:
            towns.setdefault(f"{r['c']}, {r['s']}", []).append((r["la"], r["lo"]))
    townpts = {k: [round(sum(x[0] for x in v) / len(v), 4), round(sum(x[1] for x in v) / len(v), 4)] for k, v in towns.items()}
    tags = [e for e in tagvocab.get("entries", []) if e["key"] in {t for r in rows for t in r["t"]}]
    drive = sorted([r for r in rows if r["a"] >= 1 and r["u"]], key=lambda r: (-r["a"], r["n"]))[:18]

    chips = ('<button type="button" data-tag="__sun" aria-pressed="false" title="A source says this one opens on Sunday">&#9788; Open Sunday</button>'
             '<button type="button" data-tag="__today" aria-pressed="false" title="Uses your own clock">&#128337; Open today</button>'
             '<button type="button" data-tag="__wingnight" aria-pressed="false" title="A source names a weekly wing night">&#127831; Wing night</button>'
             + "".join(f'<button type="button" data-tag="{E(t["key"])}" aria-pressed="false">{E(t["icon"])} {E(t["label"])}</button>' for t in tags))
    drive_cards = "".join(
        f'<div class="card"><b><a href="../{E(r["u"])}index.html">{E(r["n"])}</a></b>'
        f'<span class="stars" aria-hidden="true">{"●" * min(r["a"], 5)}</span> '
        f'<span class="mute" style="font-size:.82rem">{r["a"]} {"recognition" if r["a"] == 1 else "recognitions"}</span>'
        f'<div class="why">{E(", ".join(r["rb"][:4]))}</div>'
        f'<div class="why">{E(r["c"])}{", " if r["c"] else ""}{E(r["s"])} — {E(r["b"][:110])}…</div></div>' for r in drive)

    counted = {e["key"]: sum(1 for r in rows if e["key"] in r["t"]) for e in tagvocab.get("entries", [])}
    empty = [e for e in tagvocab.get("entries", []) if counted.get(e["key"], 0) == 0]
    thin = [e for e in tagvocab.get("entries", []) if 0 < counted.get(e["key"], 0) <= 3]
    gaps = ""
    if empty:
        gaps += ("No place here carries " + ", ".join(f'<b>{E(e["label"].lower())}</b>' for e in empty)
                 + ". That says nothing about America's wing counters — it says where our reading stopped. "
                 + "What would earn it: " + "; ".join(f'{E(e["label"].lower())} — {E(e["evidence"])}' for e in empty) + ". ")
    if thin:
        gaps += "Thin so far: " + ", ".join(f'{E(e["label"].lower())} ({counted[e["key"]]})' for e in thin) + ". "
    gaps += ('Every directory we read is listed on <a href="../story/free-to-use/index.html">where all of this came from</a>. '
             'A business that wants a tag it has earned can say so on its own site or in any of those directories, and we read it there.')
    body = f"""
<h1><span class="kind">Wing Country</span>Get me some wings</h1>
<p class="lede">Who's frying near you, and who's worth the gas.</p>

<div class="finder">
  <div class="row">
    <button class="btn" id="locate" type="button">📍 Where I'm at</button>
    <input id="town" type="search" list="towns" placeholder="or type a town — Buffalo, Atlanta, Nashville…" aria-label="Town">
    <datalist id="towns">{"".join(f'<option value="{E(t)}">' for t in sorted(townpts))}</datalist>
    <button class="btn ghost" id="go" type="button">Go</button>
  </div>
  <div class="chips" id="chips" role="group" aria-label="Filters">{chips}
    <button type="button" data-tag="__page" aria-pressed="false">📄 Written up here</button></div>
  <p class="mute" style="font-size:.84rem;margin:.6rem 0 0" id="status">Your browser works out where you are. The sorting happens right here in the page.</p>
</div>

<div id="out"></div>

<h2>Worth the gas</h2>
<p class="mute">Joints somebody already bragged on in print. The dots count how many said so; they're all named on the joint's own page.</p>
<div class="drive">{drive_cards}</div>

<h2 id="gaps">Thin spots</h2>
<p class="mute">{gaps}</p>
<h2>Reading the tags</h2>
<table>{"".join(f'<tr><th>{E(t["icon"])} {E(t["label"])}</th><td>{E(t["evidence"])}</td></tr>' for t in tagvocab.get("entries", []))}</table>
<p class="mute">Each tag names where it came from. No tag means we haven't read that one yet.</p>

<script>
(function(){{
var ROWS={esc_js(rows)}, TOWNS={esc_js(townpts)};
var TAGL={esc_js({e["key"]: (e["icon"] + " " + e["label"]) for e in tagvocab.get("entries", [])})};
var here=null, on={{}};
function esc(s){{return String(s==null?"":s).replace(/[&<>"]/g,function(c){{return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]}})}}
function miles(a,b,c,d){{var R=3958.8,p=Math.PI/180,x=(c-a)*p,y=(d-b)*p,
  h=Math.sin(x/2)*Math.sin(x/2)+Math.cos(a*p)*Math.cos(c*p)*Math.sin(y/2)*Math.sin(y/2);
  return 2*R*Math.asin(Math.sqrt(h))}}
var TODAY=(new Date().getDay()+6)%7;   /* JS counts Sunday 0; this week starts Monday */
function keep(r){{
  for(var k in on){{ if(!on[k]) continue;
    if(k==="__page"){{ if(!r.u) return false; }}
    else if(k==="__wingnight"){{ if(r.t.indexOf("wing-night")<0) return false; }}
    /* 'o' open, 'c' closed, 'u' nobody told us. A chip asks for OPEN, so 'u' drops out —
       a counter we have not read is not evidence of anything either way. */
    else if(k==="__sun"){{ if(r.d.charAt(6)!=="o") return false; }}
    else if(k==="__today"){{ if(r.d.charAt(TODAY)!=="o") return false; }}
    else if(r.t.indexOf(k)<0) return false; }}
  return true}}
var DAYL=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],DAY1=["M","T","W","T","F","S","S"];
function strip(d){{
  if(!d||d==="uuuuuuu")return '<span class="nohours">hours not published</span>';
  var w=176,c=(w-10)/7,o='<svg class="daystrip" viewBox="0 0 '+w+' 26" role="img" aria-label="'+
    d.split("").map(function(x,i){{return DAYL[i]+" "+({{o:"open",c:"closed",u:"not published"}}[x])}}).join(", ")+'">';
  for(var i=0;i<7;i++){{var x=i*c+(i===6?10:0),st=d.charAt(i);
    var fill=st==="o"?"var(--sauce)":"none",stroke=st==="o"?"var(--sauce)":st==="c"?"var(--mute)":"var(--line)";
    var dash=st==="u"?' stroke-dasharray="2.5 2.5"':'',col=st==="o"?"#fff":st==="c"?"var(--mute)":"var(--line)";
    o+='<rect x="'+(x+1.5).toFixed(1)+'" y="3" width="'+(c-3).toFixed(1)+'" height="18" rx="4" fill="'+fill+'" stroke="'+stroke+'" stroke-width="1.6"'+dash+'/>'+
       '<text x="'+(x+c/2).toFixed(1)+'" y="17" text-anchor="middle" fill="'+col+'" style="font:700 11px -apple-system,sans-serif">'+DAY1[i]+'</text>';}}
  return o+'</svg>';
}}
function render(){{
  var out=document.getElementById("out");
  if(!here){{out.innerHTML="";return}}
  var hits=ROWS.filter(keep).map(function(r){{var d=miles(here[0],here[1],r.la,r.lo);return {{r:r,d:d}}}})
    .sort(function(a,b){{return a.d-b.d}}).slice(0,25);
  if(!hits.length){{out.innerHTML='<p class="mute">Nothing doing. Drop a filter, or try the next town over.</p>';return}}
  out.innerHTML='<h2>Nearest first</h2>'+hits.map(function(h){{
    var r=h.r, tg=r.t.map(function(k){{return '<span class="chip">'+esc(TAGL[k]||k)+'</span>'}}).join("");
    var nm=r.u?('<a href="../'+esc(r.u)+'index.html">'+esc(r.n)+'</a>'):esc(r.n);
    var acc=r.a?(' <span class="stars" aria-hidden="true">'+"●".repeat(Math.min(r.a,5))+'</span>'):"";
    var where=[r.c,r.co?r.co+" County":"",r.s].filter(Boolean).join(" · ");
    var go=r.u?'<a class="go" href="../'+esc(r.u)+'index.html">page →</a>':(r.w?'<a class="go" href="'+esc(r.w)+'" rel="noopener">site →</a>':'<span class="go mute">not written up</span>');
    return '<div class="hit"><span class="mi">'+h.d.toFixed(1)+' mi</span><span class="nm">'+nm+acc+'</span>'+go+
      '<span class="wh">'+esc(where)+(r.b?' — '+esc(r.b.slice(0,110))+'…':'')+'</span>'+
      '<span class="wk">'+strip(r.d)+(r.so?' <em>till it runs out</em>':'')+(r.ht?' <em>'+esc(r.ht)+'</em>':(r.h?' <span class="mute">'+esc(r.h)+'</span>':''))+'</span>'+
      (tg?'<span class="tg">'+tg+'</span>':'')+'</div>';
  }}).join("");
}}
document.getElementById("chips").addEventListener("click",function(e){{
  var b=e.target.closest("button[data-tag]"); if(!b)return;
  var k=b.getAttribute("data-tag"); on[k]=!on[k]; b.setAttribute("aria-pressed",on[k]?"true":"false"); render();
}});
document.getElementById("locate").addEventListener("click",function(){{
  var s=document.getElementById("status");
  if(!navigator.geolocation){{s.textContent="This browser won't hand over a location. Type a town instead.";return}}
  s.textContent="Asking…";
  navigator.geolocation.getCurrentPosition(function(p){{
    here=[p.coords.latitude,p.coords.longitude];
    s.textContent="Sorted from where you are.";render();
  }},function(){{s.textContent="Browser said no. Type a town instead — works the same.";}},{{timeout:10000}});
}});
function bytown(){{
  var v=document.getElementById("town").value.trim(), s=document.getElementById("status");
  if(!v)return; var hit=TOWNS[v];
  if(!hit){{ var k=Object.keys(TOWNS).filter(function(t){{return t.toLowerCase().indexOf(v.toLowerCase())===0}});
    if(k.length){{hit=TOWNS[k[0]];v=k[0]}} }}
  if(!hit){{s.textContent="Nothing in this list is in a town by that name. Try the nearest big one.";return}}
  here=hit; s.textContent="Sorted from "+v+"."; render();
}}
document.getElementById("go").addEventListener("click",bytown);
document.getElementById("town").addEventListener("keydown",function(e){{if(e.key==="Enter"&&!e.isComposing){{e.preventDefault();bytown()}}}});
}})();
</script>
"""
    return page("Get me some wings — Wing Country", body, 1,
                "Wings near you, anywhere in the United States, and the counters worth a drive: naked, breaded, smoked, Black-owned, woman-owned, LGBTQ+ welcoming — every tag with its evidence.",
                [{"@context": "https://schema.org", "@type": "WebPage", "name": "Find the wings", "url": f"{site_url}/near/"}],
                f"{site_url}/near/", extra_head=f"<style>{NEAR_CSS}</style>", card="near",
                og_alt="Every wing joint in America, sorted from where you are")


# ---------------------------------------------------------------- sauce charts

def _first_class(ing: list) -> str:
    """Which class the FIRST ingredient on the label belongs to.

    A label prints an ingredient's own sub-ingredients in brackets after it —
    AGED CAYENNE RED PEPPERS (PEPPERS, VINEGAR, SALT) — so classify on the
    ingredient's own name, never on what is inside the bracket. That bracket is
    exactly why a cayenne-pepper-sauce bottle must not read as vinegar-first."""
    if not ing:
        return ""
    f = (ing[0] or "").lower().split("(")[0].split("[")[0]
    for w in ("pepper", "chile", "chili", "chilli", "gochujang", "jalapeno", "habanero", "cayenne", "sriracha"):
        if w in f:
            return "pepper"
    if "vinegar" in f or "water" in f:
        return "vinegar"
    for w in ("butter", "margarine", "oil", "cream", "mayonnaise", "buttermilk", "cheese", "yogurt"):
        if w in f:
            return "fat"
    for w in ("sugar", "syrup", "honey", "tomato", "ketchup", "catsup", "molasses", "juice concentrate"):
        if w in f:
            return "sugar"
    return "other"


def _ticks(hi: float, want=7) -> list:
    """Round numbers that fit the range: 1, 2, 2.5 or 5 times a power of ten. The old
    hard-coded list was right for grams of sugar and wrong by a factor of a hundred for
    milligrams of sodium."""
    if hi <= 0:
        return [0]
    raw = hi / want
    mag = 10 ** math.floor(math.log10(raw))
    step = next((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw), 10 * mag)
    out, t = [], 0.0
    while t <= hi + 1e-9:
        out.append(round(t, 6))
        t += step
    return out


def _tick_label(t: float) -> str:
    return f"{t:,.0f}" if t >= 10 or t == int(t) else f"{t:g}"


def strip_plot(groups: list, unit: str, width=700, rowh=46) -> str:
    """One row per base, one dot per bottle, a median tick. Position carries the magnitude;
    one hue, because the rows are already labelled."""
    vals = [v for _, pts in groups for v, _ in pts]
    if not vals:
        return ""
    lo, hi = 0, max(vals) * 1.08
    left, right = 168, 24
    w = width
    h = len(groups) * rowh + 56
    px = lambda v: left + (v - lo) / (hi - lo) * (w - left - right)
    ticks = _ticks(hi)
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Sugar per tablespoon, one dot per bottle, grouped by sauce base">']
    for t in ticks:
        out.append(f'<line class="grid" x1="{px(t):.1f}" y1="14" x2="{px(t):.1f}" y2="{h - 40}"/>'
                   f'<text class="axis" x="{px(t):.1f}" y="{h - 24}" text-anchor="middle">{_tick_label(t)}</text>')
    out.append(f'<text class="axis" x="{left}" y="{h - 6}">{E(unit)}</text>')
    for i, (label, pts) in enumerate(groups):
        y = 32 + i * rowh
        out.append(f'<text class="rowlab" x="0" y="{y + 4}">{E(label)}</text>')
        if pts:
            med = statistics.median([v for v, _ in pts])
            out.append(f'<line class="med" x1="{px(med):.1f}" y1="{y - 13}" x2="{px(med):.1f}" y2="{y + 13}"><title>median {med:.1f}</title></line>')
            out.append(f'<text class="vallab" x="{px(med):.1f}" y="{y - 17}" text-anchor="middle">{med:,.4g}</text>')
        seen: dict = {}
        for v, name in sorted(pts):
            k = round(px(v) / 7)
            off = seen.get(k, 0)
            seen[k] = off + 1
            dy = (off % 3 - 1) * 7
            out.append(f'<circle class="dot" cx="{px(v):.1f}" cy="{y + dy}" r="5"><title>{E(name)} — {v:,.4g} {E(unit.split(",")[0])}</title></circle>')
    out.append("</svg>")
    return "".join(out)


def stacked_first(groups: list, dark=False, width=700) -> str:
    """Part-to-whole: what is the first ingredient on the label, by base. 2px surface gaps,
    direct labels on segments wide enough, a legend, and a table twin beside it."""
    left, right, barh, gap = 168, 30, 26, 16
    w = width
    h = len(groups) * (barh + gap) + 24
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="First ingredient on the label, share of bottles, by sauce base">']
    for i, (label, counts, total) in enumerate(groups):
        y = 8 + i * (barh + gap)
        out.append(f'<text class="rowlab" x="0" y="{y + barh - 8}">{E(label)}</text>')
        x = left
        span = w - left - right
        for key, lab, cl, cd in FIRST_CLASSES:
            n = counts.get(key, 0)
            if not n:
                continue
            bw = n / total * span
            col = cd if dark else cl
            out.append(f'<rect class="seg" x="{x:.1f}" y="{y}" width="{max(bw - 2, 1):.1f}" height="{barh}" rx="4" fill="{col}">'
                       f'<title>{E(label)}: {n} of {total} bottles, {lab.lower()}</title></rect>')
            if bw > 44:
                out.append(f'<text class="vallab" x="{x + bw / 2:.1f}" y="{y + barh / 2 + 4:.1f}" text-anchor="middle" style="fill:#fff">{n}</text>')
            x += bw
        out.append(f'<text class="vallab" x="{w - right + 6}" y="{y + barh / 2 + 4:.1f}">{total}</text>')
    out.append("</svg>")
    return "".join(out)


def sauce_map_multiples(states_geo: dict, by_base: dict, width=250) -> str:
    """Small multiples: one little United States per base, dots where the makers are.
    One series per panel, so the panel title carries identity and no categorical palette
    is needed. Alaska and Hawaii are dropped from these panels — at this size they cost
    more room than they carry, and the caption says so."""
    fit = usmap.fit_states(states_geo, width)
    h = fit["h"]
    shells = []
    for iso, name, d in usmap.state_paths(states_geo, fit):
        if usmap.zone_of_state(iso) != "l48":
            continue
        shells.append(d)
    paths = "".join(f'<path class="st" d="{d}"/>' for d in shells)
    out = ['<div class="smallmult">']
    for key, label, gloss in BASES:
        pts = by_base.get(key) or []
        if not pts:
            continue
        dots = []
        for sc in pts:
            if sc.get("lat") is None:
                continue
            x, y = usmap.project(sc["lon"], sc["lat"], fit)
            if 0 <= x <= width and 0 <= y <= h:
                dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="var(--sauce)" stroke="var(--bg)" stroke-width="1.4">'
                            f'<title>{E(sc["name"])} — {E(sc.get("maker", ""))}, {E(sc.get("town", ""))}</title></circle>')
        out.append(f'<figure><figcaption>{E(label)} <small>{len(pts)} bottle{"s" if len(pts) != 1 else ""} · {E(gloss)}</small></figcaption>'
                   f'<svg viewBox="0 0 {width} {h:.0f}" role="img" aria-label="Makers of {E(label)} sauce across the United States">'
                   f'<style>.st{{fill:var(--chip);stroke:var(--mute);stroke-width:.6}}</style>'
                   f'{paths}{"".join(dots)}</svg></figure>')
    out.append("</div>")
    return "".join(out)


def sauce_page(page, sauces: dict, recs: list, states_geo: dict, site_url: str) -> str:
    rows = list((sauces or {}).get("sauces", []))
    sauce_recs = [r for r in recs if r["type"] == "sauce"]
    body = ['<h1><span class="kind">Wing Country</span>What&#8217;s in the bottle</h1>',
            '<p class="lede">Every number here came off a label. Who wins gets argued elsewhere, at length.</p>']
    if not rows:
        body.append('<p class="mute">No labels read yet. The sauce pages are up though: '
                    + " · ".join(f'<a href="../sauce/{E(r["id"])}/index.html">{E(r["names"]["name"])}</a>' for r in sauce_recs) + "</p>")
        return page("What's in the bottle — Wing Country", "".join(body), 1, "Wing sauce measured off the label.", None, f"{site_url}/sauce/",
                    extra_head=f"<style>{CHART_CSS}</style>", card="sauce")

    withsalt = [x for x in rows if x.get("sodium_mg_per_tbsp") is not None]
    withsugar = [x for x in rows if x.get("sugar_g_per_tbsp") is not None]
    withing = [x for x in rows if x.get("ingredients")]
    withscov = [x for x in rows if x.get("scoville") is not None]
    body.append('<div class="facts">'
                + "".join(f'<div class="fact"><div class="n">{n}</div><div class="l">{E(l)}</div></div>' for n, l in
                          [(len(rows), "bottles read"), (len(withing), "with an ingredient list"),
                           (len(withsalt), "with salt on the panel"), (len(withsugar), "with sugar on the panel"),
                           (len(withscov), "with a published Scoville number")])
                + "</div>")

    # chart 1 — salt per tablespoon, the number every wing sauce publishes
    groups = []
    for key, label, _ in BASES:
        pts = [(x["sodium_mg_per_tbsp"], f'{x["name"]} ({x.get("maker", "")})') for x in withsalt if x.get("base") == key]
        if pts:
            groups.append((label, pts))
    if groups:
        allv = [v for _, pts in groups for v, _ in pts]
        med = statistics.median(allv)
        top = max(withsalt, key=lambda x: x["sodium_mg_per_tbsp"])
        spoon = [x for x in withsalt if (x.get("serving_tbsp") or 1) < 0.25]
        body.append('<div class="viz"><h3>Salt, by the tablespoon</h3>'
                    f'<p class="note">One dot per bottle, {len(allv)} in all; the upright tick marks its row\'s median. '
                    f'Across every bottle the median runs {med:,.0f} mg a tablespoon, against the 2,300 mg the FDA counts as a day. '
                    f'{E(top["name"])} tops it at {top["sodium_mg_per_tbsp"]:,.0f} mg. '
                    + (f'Careful with the far right: {len(spoon)} of these are dry seasonings whose own serving is a quarter teaspoon or less, '
                       'scaled to a tablespoon here so they sit on the same axis. Nobody eats a tablespoon of them. '
                       if spoon else '')
                    + 'Hover a dot for the bottle.</p>'
                    + strip_plot(groups, "milligrams of sodium per tablespoon")
                    + '<details class="tbl"><summary>The same numbers as a table</summary><table><tr><th>Sauce</th><th>Maker</th><th>Base</th><th>Sodium mg/tbsp</th></tr>'
                    + "".join(f'<tr><td>{E(x["name"])}</td><td>{E(x.get("maker", ""))}</td><td>{E(BASE_LABEL.get(x.get("base", ""), x.get("base", "")))}</td><td>{x["sodium_mg_per_tbsp"]:,.0f}</td></tr>'
                              for x in sorted(withsalt, key=lambda x: -x["sodium_mg_per_tbsp"]))
                    + "</table></details></div>")

    # chart 2 — sugar per tablespoon, the axis the sweet half of the menu runs on
    g_sug = []
    for key, label, _ in BASES:
        pts = [(x["sugar_g_per_tbsp"], f'{x["name"]} ({x.get("maker", "")})') for x in withsugar if x.get("base") == key]
        if pts:
            g_sug.append((label, pts))
    if g_sug:
        allv = [v for _, pts in g_sug for v, _ in pts]
        body.append('<div class="viz"><h3>Sugar, by the tablespoon</h3>'
                    f'<p class="note">The same bottles on the other axis, {len(allv)} of them. A tablespoon of table sugar holds about 12.6 g, '
                    'so a bottle out at the right-hand end is most of the way to syrup. A cayenne sauce sits at zero and a honey-barbecue '
                    'sits where the sweet is. Same wing, two different foods.</p>'
                    + strip_plot(g_sug, "grams of sugar per tablespoon")
                    + '<details class="tbl"><summary>The same numbers as a table</summary><table><tr><th>Sauce</th><th>Maker</th><th>Base</th><th>Sugar g/tbsp</th></tr>'
                    + "".join(f'<tr><td>{E(x["name"])}</td><td>{E(x.get("maker", ""))}</td><td>{E(BASE_LABEL.get(x.get("base", ""), x.get("base", "")))}</td><td>{x["sugar_g_per_tbsp"]:g}</td></tr>'
                              for x in sorted(withsugar, key=lambda x: -x["sugar_g_per_tbsp"]))
                    + "</table></details></div>")

    # chart 3 — what is first on the label
    g2 = []
    for key, label, _ in BASES:
        counts: dict = {}
        for x in withing:
            if x.get("base") != key:
                continue
            c = _first_class(x["ingredients"])
            counts[c] = counts.get(c, 0) + 1
        tot = sum(counts.values())
        if tot:
            g2.append((label, counts, tot))
    if g2:
        leg = '<div class="legend-row">' + "".join(
            f'<span><i style="background:{cl}"></i>{E(lab)}</span>' for _, lab, cl, _ in FIRST_CLASSES) + "</div>"
        body.append('<div class="viz"><h3>What comes first on the label</h3>'
                    '<p class="note">A label lists ingredients in descending order by weight, so the first word states the sauce\'s whole argument. '
                    'Watch for the bracket: aged cayenne peppers are printed with their own vinegar inside the bracket, which is a pepper sauce, not a vinegar one. '
                    'Numbers on the segments count bottles; the number at the right is the row total.</p>'
                    + leg + stacked_first(g2)
                    + '<details class="tbl"><summary>The same counts as a table</summary><table><tr><th>Base</th>'
                    + "".join(f"<th>{E(lab)}</th>" for _, lab, _, _ in FIRST_CLASSES) + "<th>Bottles</th></tr>"
                    + "".join(f'<tr><td>{E(lab)}</td>' + "".join(f'<td>{c.get(k, 0)}</td>' for k, _, _, _ in FIRST_CLASSES) + f"<td>{t}</td></tr>" for lab, c, t in g2)
                    + "</table></details></div>")

    # chart 4 — where the makers are
    by_base: dict = {}
    for x in rows:
        if x.get("lat") is not None:
            by_base.setdefault(x.get("base", "other"), []).append(x)
    if by_base:
        body.append('<div class="viz"><h3>Where the makers are</h3>'
                    '<p class="note">One little country per sauce. A dot marks a bottler\'s town, not a restaurant; several bottles from one town sit on one dot.</p>'
                    + sauce_map_multiples(states_geo, by_base)
                    + '<figcaption>Lower forty-eight only on these panels. State outlines: Natural Earth, public domain. '
                      'Towns geocoded from OpenStreetMap, ODbL.</figcaption></div>')

    # the Scoville gap, stated rather than filled
    body.append('<h2>Heat nobody measures</h2>'
                f'<p class="mute">{len(withscov)} of {len(rows)} bottles carry a Scoville number anybody publishes. '
                'Scoville heat units come from a lab assay of capsaicin, and almost no wing-sauce maker pays for one; the word on the front '
                '— mild, medium, hot, and whatever a challenge sauce calls itself — is a maker\'s claim about its own product and nothing more. '
                'Each claim sits on its sauce\'s page as <code>heat_claim</code>, in the maker\'s own words.</p>')

    # the ranks table
    body.append('<h2>Every bottle we read</h2><p class="mute">1 means first on the label. A dash means it isn&#8217;t on there. '
                'Blank means we couldn&#8217;t find a label.</p>'
                '<div style="overflow-x:auto"><table><tr><th>Sauce</th><th>Maker</th><th>Town</th><th>Base</th><th>Pepper</th><th>Vinegar</th><th>Fat</th><th>Sugar</th><th>Soy</th><th>Sodium mg/tbsp</th><th>Sugar g/tbsp</th><th>Label</th></tr>'
                + "".join(
                    "<tr><td>" + E(x["name"]) + "</td><td>" + E(x.get("maker", "")) + "</td><td>" + E((x.get("town") or "") + (", " + x["state"] if x.get("state") else "")) + "</td><td>"
                    + E(BASE_LABEL.get(x.get("base", ""), x.get("base", ""))) + "</td>"
                    + "".join("<td>" + ("\u2014" if x.get(k) == 0 else ("" if x.get(k) is None else str(x[k]))) + "</td>" for k in ("pepper_rank", "vinegar_rank", "fat_rank", "sugar_rank", "soy_rank"))
                    + "<td>" + ("" if x.get("sodium_mg_per_tbsp") is None else f'{x["sodium_mg_per_tbsp"]:,.0f}') + "</td>"
                    + "<td>" + ("" if x.get("sugar_g_per_tbsp") is None else f'{x["sugar_g_per_tbsp"]:g}') + "</td>"
                    + "<td>" + (f'<a href="{E(x["source_url"])}" rel="noopener">seen here</a>' if x.get("source_url") else "") + "</td></tr>"
                    for x in sorted(rows, key=lambda x: (x.get("base") or "", x["name"])))
                + "</table></div>")

    body.append('<h2>The bottles</h2><div class="cards">' + "".join(
        f'<div class="card"><a class="t" href="../sauce/{E(r["id"])}/index.html">{E(r["names"]["name"])}</a><p>{E(r["blurb"][:160])}</p></div>' for r in sauce_recs) + "</div>")
    body.append('<p class="legend">Labels were read on the makers\' own pages, on retailers\' product pages and in the USDA\'s FoodData Central branded-food panels, '
                'which are public domain; each row links to the page it was read from, and the date sits on the sauce\'s own entry. '
                'Nutrition Facts round sugar to the gram, so a bottle showing 0 g may hold a little. The data is at <a href="../api/sauces.json">api/sauces.json</a>.</p>')
    return page("Read the bottle — Wing Country", "".join(body), 1,
                "American wing sauce measured off the label: sodium and sugar per tablespoon, what comes first on the ingredient list, and where the makers are.",
                [{"@context": "https://schema.org", "@type": "Dataset", "name": "American wing sauce labels", "url": f"{site_url}/sauce/",
                  "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": f"{site_url}/api/sauces.json"}]}],
                f"{site_url}/sauce/", extra_head=f"<style>{CHART_CSS}</style>", card="sauce",
                og_alt="Salt, sugar, pepper and fat measured off American wing sauce labels")


# ---------------------------------------------------------------- the quiz

def quiz_page(page, quiz: dict, by_id: dict, site_url: str) -> str:
    qs = quiz["questions"]
    res = quiz["results"]
    forms = []
    for i, q in enumerate(qs):
        opts = "".join(
            f'<label class="opt"><input type="radio" name="q{i}" value="{i}-{j}"> {E(a["t"])}</label>' for j, a in enumerate(q["a"]))
        forms.append(f'<fieldset class="qz"><legend>{i + 1}. {E(q["q"])}</legend>{opts}</fieldset>')
    scoring = [[a["s"] for a in q["a"]] for q in qs]
    results = {k: {"title": v["title"], "say": v["say"], "url": f"../style/{k}/index.html"} for k, v in res.items() if k in by_id}
    body = f"""
<h1><span class="kind">Wing Country</span>{E(quiz["title"])}</h1>
<p class="lede">{E(quiz["lede"])}</p>
<form id="qz">{"".join(forms)}
<div class="cta"><button class="btn" id="tally" type="button">Tally it up</button><button class="btn ghost" id="again" type="button">Start over</button></div></form>
<div id="verdict" aria-live="polite"></div>
<p class="legend">The scoring runs in your browser. Each result links to a style page, where the sources sit.</p>
<style>
.qz{{border:1px solid var(--line);border-radius:12px;background:var(--panel);padding:.8rem 1rem;margin:.9rem 0}}
.qz legend{{font-weight:600;padding:0 .4rem}}
.opt{{display:block;padding:.35rem .2rem;cursor:pointer}}
.opt input{{margin-right:.55rem}}
.verdict{{background:var(--panel);border:2px solid var(--sauce);border-radius:14px;padding:1rem 1.2rem;margin:1rem 0}}
.verdict h2{{margin:.1rem 0 .3rem;border:0}}
.bars{{margin-top:.7rem}}
.bars div{{display:grid;grid-template-columns:11rem 1fr auto;gap:.6rem;align-items:center;margin:.25rem 0;font-size:.9rem}}
.bars i{{display:block;height:.7rem;border-radius:4px;background:var(--sauce)}}
</style>
<script>
(function(){{
var S={esc_js(scoring)}, R={esc_js(results)};
function esc(s){{return String(s==null?"":s).replace(/[&<>"]/g,function(c){{return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]}})}}
document.getElementById("tally").addEventListener("click",function(){{
  var sc={{}}, answered=0;
  S.forEach(function(q,i){{
    var el=document.querySelector('input[name="q'+i+'"]:checked'); if(!el)return; answered++;
    var j=parseInt(el.value.split("-")[1],10), s=q[j];
    for(var k in s) sc[k]=(sc[k]||0)+s[k];
  }});
  var v=document.getElementById("verdict");
  if(!answered){{v.innerHTML='<p class="mute">Answer at least one.</p>';return}}
  var rank=Object.keys(sc).sort(function(a,b){{return sc[b]-sc[a]}});
  var top=rank[0], max=sc[top], r=R[top]||{{title:top,say:"",url:"#"}};
  var bars=rank.map(function(k){{var w=Math.round(sc[k]/max*100);
    return '<div><span>'+esc((R[k]||{{}}).title||k)+'</span><i style="width:'+w+'%"></i><span>'+sc[k]+'</span></div>'}}).join("");
  v.innerHTML='<div class="verdict"><h2>'+esc(r.title)+'</h2><p>'+esc(r.say)+'</p>'+
    '<p><a class="btn" href="'+esc(r.url)+'">Read the style →</a></p><div class="bars">'+bars+'</div></div>';
  v.scrollIntoView({{behavior:"smooth",block:"nearest"}});
}});
document.getElementById("again").addEventListener("click",function(){{
  document.getElementById("qz").reset(); document.getElementById("verdict").innerHTML="";
}});
}})();
</script>
"""
    return page(f'{quiz["title"]} — Wing Country', body, 1, quiz["lede"], None, f"{site_url}/quiz/", card="quiz",
                og_alt="Which wing claims you? A six-question American wing quiz")


# ---------------------------------------------------------------- the bird

# A wing, drawn as three capsules in a shallow Z, the way it lies on a board. Each capsule
# is one round-capped line, so a part can be painted on its own while the outline still
# runs unbroken around the whole wing.
# (key, x1, y1, x2, y2, thickness, label, gloss, label x, label y)
WING_PARTS = [
    ("drumette", 78, 168, 178, 108, 44, "drumette",
     "the piece nearest the body, one bone, meat pushed to one end — a little drumstick", 96, 232),
    ("flat", 178, 108, 296, 132, 34, "flat",
     "the middle piece, two thin bones, the most skin per bite; Buffalo calls it a wingette, a butcher calls it a flat", 246, 52),
    ("tip", 296, 132, 368, 166, 15, "tip",
     "the pointed end, skin and cartilage, cut off into the stockpot at most counters", 384, 122),
]
WING_JOINTS = ((178, 108, 25), (296, 132, 20))


def wing_svg(lit: set, width=420, label=True, ident="") -> str:
    """One chicken wing. Parts in `lit` get painted sauce-coloured, the rest recede.
    Emphasis, not categories — so no palette is needed and none is used."""
    out = [f'<svg viewBox="0 0 420 250" role="img" aria-label="A chicken wing laid out flat; '
           f'{", ".join(sorted(lit)) if lit else "no part"} marked">']
    # rim first as a fat stroke, then the fill on top, so the wing keeps one clean outer edge
    for key, x1, y1, x2, y2, t, *_ in WING_PARTS:
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--ink)" stroke-width="{t + 7}" stroke-linecap="round"/>')
    for cx, cy, r in WING_JOINTS:
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r + 3.5}" fill="var(--ink)"/>')
    for key, x1, y1, x2, y2, t, *_ in WING_PARTS:
        col = "var(--sauce)" if key in lit else "var(--chip)"
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{t}" stroke-linecap="round"/>')
    for cx, cy, r in WING_JOINTS:
        # the knuckle: a pale bone end with an ink rim, never a hole
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="var(--chip)"/>')
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r - 6}" fill="none" stroke="var(--mute)" stroke-width="1.6" opacity=".7"/>')
    if label:
        for key, x1, y1, x2, y2, t, lab, _, lx, ly in WING_PARTS:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            out.append(f'<line x1="{lx}" y1="{ly + (6 if ly < my else -12)}" x2="{mx:.0f}" y2="{my:.0f}" '
                       f'stroke="var(--mute)" stroke-width="1.5" stroke-dasharray="4 3"/>')
            out.append(f'<circle cx="{mx:.0f}" cy="{my:.0f}" r="3" fill="var(--mute)"/>')
            anchor = "end" if lx > 370 else "middle"
            out.append(f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" fill="var(--ink)" '
                       f'style="font:700 15px Futura,\'Century Gothic\',\'Avenir Next\',sans-serif">{E(lab)}</text>')
    out.append("</svg>")
    return "".join(out)


# (style id, label, parts served, the sentence under the drawing)
WING_STYLES = [
    ("buffalo", "Buffalo", {"drumette", "flat"},
     "Cut at both joints, tip to the stockpot, fried bare, shaken in butter and cayenne sauce."),
    ("rochester-breaded", "Rochester", {"drumette", "flat"},
     "Same two pieces, dredged before they hit the oil — the line Buffalo draws and Rochester crosses."),
    ("korean-american", "Korean American", {"drumette", "flat", "tip"},
     "Often the whole wing, tip attached, fried twice so the crust goes thin and stays hard under a wet glaze."),
    ("caribbean-jerk", "Jerk", {"drumette", "flat", "tip"},
     "Marinated whole, tip and all, then grilled or roasted rather than dropped in a fryer."),
    ("smoked-bbq-wing", "The barbecue joint", {"drumette", "flat", "tip"},
     "Whole wings go on the smoker, because a tip that crisps in smoke is worth eating."),
    ("atlanta-lemon-pepper", "Atlanta", {"drumette", "flat"},
     "Party wings out of a bag, fried hard, shaken in seasoning or dunked in butter for wet."),
    ("memphis-dry-rub", "Memphis", {"drumette", "flat", "tip"},
     "Rubbed before the cook and dusted again after, off the same counter as the ribs."),
]


def wing_page(page, by_id: dict, site_url: str) -> str:
    cuts = [i for i in ("wing-cut", "naked-fry", "breaded-fry", "double-fry", "the-toss", "frying-oil") if i in by_id]
    words = [i for i in ("drumette", "flat", "wing-tip", "flapper", "party-wing", "all-flats") if i in by_id]
    body = ['<h1><span class="kind">Wing Country</span>Flat or drum?</h1>',
            '<p class="lede">One wing, three pieces. Order twenty and you&#8217;ve had a wing off ten birds.</p>',
            '<div class="viz"><h3>The wing, divided</h3>'
            '<p class="note">Shoulder end at the left. The rings are where the knife goes.</p>'
            + '<div style="max-width:620px;margin:0 auto">' + wing_svg(set(), ident="all") + "</div>"
            + '<table style="margin-top:.8rem">'
            + "".join(f"<tr><th>{E(lab)}</th><td>{E(gloss)}</td></tr>" for _, _, _, _, _, _, lab, gloss, _, _ in WING_PARTS)
            + "</table></div>"]
    body.append('<div class="viz"><h3>One bird, one of each</h3>'
                '<p class="note">No bird gives two flats. Every drum a shop sells came with a flat attached, which is why all-flats costs extra — '
                'and why somebody, somewhere, is eating the drums. <a href="../story/the-flat-and-the-drum/index.html">The whole fight →</a></p></div>')
    body.append('<div class="smallmult" style="grid-template-columns:repeat(auto-fit,minmax(17rem,1fr))">')
    for sid, label, lit, gloss in WING_STYLES:
        rec = by_id.get(sid)
        link = f'<a href="../style/{E(sid)}/index.html">{E(label)}</a>' if rec else E(label)
        body.append(f'<figure><figcaption>{link} <small>{E("whole wing" if len(lit) == 3 else ", ".join(sorted(lit)))}</small></figcaption>'
                    + wing_svg(lit, width=420, label=False, ident=sid)
                    + f'<figcaption style="font-weight:400;margin-top:.4rem">{E(gloss)}</figcaption></figure>')
    body.append("</div>")
    if cuts:
        body.append('<h2>Out back</h2><div class="cards">' + "".join(
            f'<div class="card"><a class="t" href="../fry/{E(c)}/index.html">{E(by_id[c]["names"]["name"])}</a>'
            f'<p>{E(by_id[c]["blurb"][:170])}</p></div>' for c in cuts) + "</div>")
    if words:
        body.append('<h2>What to call \&#8217;em</h2><div class="cards">' + "".join(
            f'<div class="card"><a class="t" href="../word/{E(c)}/index.html">{E(by_id[c]["names"]["name"])}</a>'
            f'<p>{E(by_id[c]["blurb"][:170])}</p></div>' for c in words) + "</div>")
    body.append('<p class="legend">Our drawing, and a diagram rather than a butcher\'s chart — the lines mark where styles differ. '
                'For the seams, read a poultry cutting guide from a state extension service.</p>')
    return page("Flat or drum? — Wing Country", "".join(body), 1,
                "A diagram of the chicken wing — drumette, flat and tip — and which pieces each American wing style serves.",
                None, f"{site_url}/wing/", extra_head=f"<style>{CHART_CSS}</style>", card="wing",
                og_alt="A chicken wing laid out flat with the drumette, the flat and the tip named")


# ---------------------------------------------------------------- the numbers

import viz  # noqa: E402


def numbers_page(page, recs: list, places: dict, geo: dict, site_url: str, site_dir) -> str:
    import collections
    import re as _re

    pl = places["places"]
    by_id = {r["id"]: r for r in recs}

    # 1 — how near the nearest wing counter is, anywhere in the country
    out_png = site_dir / "viz" / "near-the-nearest-wing.png"
    stats = viz.distance_png(geo, pl, out_png)

    # 2 — when the pits opened
    years = []
    for r in recs:
        y = (r.get("facets") or {}).get("founded")
        if r["type"] == "place" and y and _re.fullmatch(r"\d{4}", str(y)):
            years.append((int(y), r["names"]["name"]))

    # 3 — what the recipes call for
    stop = {"teaspoon", "teaspoons", "tablespoon", "tablespoons", "tbsp", "tsp", "cups", "cup", "quart", "pound",
            "pounds", "ounce", "ounces", "optional", "ground", "minced", "chopped", "finely", "taste", "large",
            "small", "fresh", "about", "into", "with", "plus", "each", "more", "than", "very", "well", "your",
            "prepared", "granulated", "packed", "pieces", "piece", "inch", "size", "good", "half", "them", "from"}
    words = collections.Counter()
    nrec = 0
    for r in recs:
        for rc in r.get("recipes", []):
            nrec += 1
            seen = set()
            for i in rc.get("ingredients", []):
                for wd in _re.findall(r"[a-z]{4,}", i.lower()):
                    if wd not in stop:
                        seen.add(wd)
            words.update(seen)
    ing_rows = [(w, c) for w, c in words.most_common(16)]

    # 4 — which days a wing counter is open
    known = [p for p in pl if any(v != "unknown" for v in (p.get("days") or {}).values())]
    nh = len(known)
    days = {d: sum(1 for p in known if (p.get("days") or {}).get(d) == "open") for d in viz.DAYS}
    closed_su = sum(1 for p in known if (p.get("days") or {}).get("Su") == "closed")
    unk_su = len(pl) - nh
    day_rows = [(viz.DAY_NAME[d], days[d]) for d in viz.DAYS]

    # 5 — which kinds of page point at which
    edges = []
    for r in recs:
        for k in r.get("kin_out", []):
            t = by_id.get(k["to"])
            if t:
                edges.append({"from_type": r["type"], "to_type": t["type"]})
    order = ["style", "sauce", "dish", "fry", "place", "person", "org", "event", "term", "art", "story"]
    present = [t for t in order if any(e["from_type"] == t or e["to_type"] == t for e in edges)]
    labels = {"style": "styles", "sauce": "sauces", "dish": "dishes", "fry": "the kitchen", "place": "places",
              "person": "people", "org": "orgs", "event": "events", "term": "words", "art": "art", "story": "stories"}

    # a few numbers worth stating plainly
    lat_lon = [(p["lat"], p["lon"]) for p in pl if p.get("lat") is not None]
    import math as _m
    nearest = []
    for i, (a, b) in enumerate(lat_lon):
        best = min(((a - c) * 69) ** 2 + ((b - d) * 69 * _m.cos(_m.radians(a))) ** 2
                   for j, (c, d) in enumerate(lat_lon) if i != j)
        nearest.append(_m.sqrt(best))
    nearest.sort()
    med_gap = nearest[len(nearest) // 2] if nearest else 0

    body = ['<h1><span class="kind">Wing Country</span>Do the math</h1>',
            '<p class="lede">Adding it up.</p>',
            '<div class="facts">'
            + "".join(f'<div class="fact"><div class="n">{n}</div><div class="l">{E(l)}</div></div>' for n, l in [
                (f"{stats['median']:.0f} mi", "median distance to a wing counter, lower forty-eight"),
                (f"{med_gap:.1f} mi", "median distance from one counter to the next"),
                (len(pl), "places"), (nrec, "recipes"), (len(edges), "links between pages")])
            + "</div>"]

    body.append('<div class="viz"><h3>Distance to a wing</h3>'
                f'<p class="note">Every point in the lower forty-eight, shaded by the distance to the closest of the {len(lat_lon)} places on the map. '
                f'Black dots are the places themselves. Half the country sits within {stats["median"]:.0f} miles of one.</p>'
                f'<img src="../viz/near-the-nearest-wing.png" alt="A map of the United States shaded by distance to the nearest wing counter; the eastern seaboard and the Great Lakes run dark, the Great Basin and the high plains pale." style="width:100%;border-radius:10px;display:block">'
                + viz.ramp_legend(stats["cuts"], stats["ramp"], "miles to the nearest wing counter")
                + '<details class="tbl"><summary>The far corners</summary><table><tr><th>Miles to a wing</th><th>Where</th></tr>'
                + "".join(f'<tr><td>{mi:.0f}</td><td>{lat:.2f}, {lon:.2f}</td></tr>' for mi, lat, lon in stats["worst"])
                + '</table></details></div>')

    if years:
        body.append('<div class="viz"><h3>Founding years</h3>'
                    f'<p class="note">The {len(years)} places here whose founding year is on a page. Stems stack where a year is crowded. '
                    'Hover one for the name.</p>' + viz.timeline_svg(years)
                    + '<details class="tbl"><summary>By decade</summary><table><tr><th>Decade</th><th>Pits</th></tr>'
                    + "".join(f"<tr><td>{d}s</td><td>{c}</td></tr>" for d, c in sorted(collections.Counter((y // 10) * 10 for y, _ in years).items()))
                    + "</table></details></div>")

    body.append('<div class="viz"><h3>Ingredients, by how many recipes call for them</h3>'
                f'<p class="note">Across {nrec} recipes, counting each ingredient once per recipe. Measures and cutting words are dropped.</p>'
                + viz.bars_svg(ing_rows, unit="recipes calling for it")
                + '<details class="tbl"><summary>As a table</summary><table><tr><th>Ingredient word</th><th>Recipes</th></tr>'
                + "".join(f"<tr><td>{E(w)}</td><td>{c}</td></tr>" for w, c in ing_rows) + "</table></details></div>")

    body.append('<div class="viz"><h3>Days open</h3>'
                f'<p class="note">From the {nh} places whose days we could read. A wing counter keeps the weekend and most of the week. '
                f'{closed_su} of the {nh} shut on Sunday; another {unk_su} have no published days at all, and those draw as blanks. '
                'A blank means unread, and the filters leave it out.</p>'
                + viz.bars_svg(day_rows, unit="places open", left=140)
                + '<details class="tbl"><summary>As a table</summary><table><tr><th>Day</th><th>Open</th></tr>'
                + "".join(f"<tr><td>{E(d)}</td><td>{c}</td></tr>" for d, c in day_rows) + "</table></details></div>")

    body.append('<div class="viz"><h3>Kin, by kind of page</h3>'
                f'<p class="note">Every one of the {len(edges)} links between pages, by the kind of page at each end. '
                'The row points at the column.</p>'
                + viz.kin_matrix_svg(edges, present, labels) + "</div>")

    body.append('<p class="legend">The distance map is computed on a grid clipped to the states\' own outlines '
                '(Natural Earth, public domain) and measured against every place on the map, most of which come from OpenStreetMap under the ODbL. '
                'Everything else is counted straight out of <a href="../api/nodes.json">the records</a>.</p>')
    return page("Do the math — Wing Country", "".join(body), 1,
                "American wings counted: how near the nearest counter sits anywhere in the country, when the places opened, what the recipes call for, which days they open.",
                None, f"{site_url}/numbers/", extra_head=f"<style>{CHART_CSS}</style>", card="numbers",
                og_alt="A map of the United States shaded by distance to the nearest wing counter")


# ---------------------------------------------------------------- make a sauce

MAKE_CSS = """
.dials{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:1rem;background:var(--panel);
  border:1px solid var(--line);border-radius:14px;padding:1rem 1.1rem;margin:.6rem 0 1.2rem}
.dial b{display:block;font-size:.78rem;text-transform:uppercase;letter-spacing:.14em;color:var(--gold);
  font-family:var(--sign,sans-serif);margin-bottom:.4rem}
.dial .opts{display:flex;flex-wrap:wrap;gap:.35rem}
.dial button{font:inherit;font-size:.86rem;font-family:var(--ui,sans-serif);padding:.32rem .72rem;border-radius:999px;
  border:1.5px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer}
.dial button[aria-pressed=true]{background:var(--sauce);border-color:var(--sauce);color:#fff}
.recipe{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1.2rem 1.3rem}
.recipe h3{margin:.1rem 0 .1rem;font-size:1.3rem}
.recipe .says{color:var(--mute);font-style:italic;margin:0 0 .9rem}
.recipe ul{list-style:none;margin:.2rem 0 1rem;padding:0}
.recipe li{display:flex;gap:.7rem;padding:.3rem 0;border-bottom:1px dotted var(--line);font-size:1rem}
.recipe li .q{flex:0 0 9.5rem;text-align:right;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap}
@media(max-width:520px){.recipe li{flex-direction:column;gap:0}.recipe li .q{text-align:left;flex:none}}
.recipe li.zero{display:none}
.recipe ol{margin:.2rem 0 1rem;padding-left:1.2rem}.recipe ol li{display:list-item;border:0;padding:.15rem 0}
.recipe .prov{font-size:.85rem;color:var(--mute);border-top:1px solid var(--line);padding-top:.7rem;margin-top:.4rem}
.sugarline{display:flex;align-items:baseline;gap:.6rem;flex-wrap:wrap;margin:.2rem 0 .3rem}
.sugarline b{font-size:1.5rem;font-family:var(--display,serif)}
.nearby{font-size:.88rem;color:var(--mute);margin:.5rem 0 0}
.mk-actions{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:1rem}
"""


MAKE_TABS_CSS = """
.tabs{display:flex;gap:.4rem;margin:.2rem 0 1rem}
.tabs button{font:inherit;font-family:var(--sign,sans-serif);font-size:.95rem;letter-spacing:.04em;padding:.5rem 1.1rem;
  border-radius:999px;border:2px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer}
.tabs button[aria-selected=true]{background:var(--sauce);border-color:var(--sauce);color:#fff}
.panel[hidden]{display:none}
.carolina-note{background:var(--panel);border-left:5px solid var(--gold);border-radius:0 12px 12px 0;padding:.8rem 1rem;margin:.2rem 0 1rem;font-size:.95rem}
.per{font-size:.86rem;color:var(--mute);margin:.1rem 0 .8rem}
"""


def make_page(page, builder: dict, sauces: dict, recs: list, site_url: str, rub: dict | None = None, dip: dict | None = None) -> str:
    by_id = {r["id"]: r for r in recs}
    # every bottle we measured, so the result can be put beside them
    bottles = [{"n": s["name"], "b": s.get("base"), "g": s.get("sugar_g_per_tbsp")}
               for s in sauces.get("sauces", []) if s.get("sugar_g_per_tbsp") is not None]
    for b in builder["bases"]:
        rec = by_id.get(b["sauce"])
        b["href"] = f"../sauce/{b['sauce']}/index.html" if rec else ""
        st = by_id.get(b["style"])
        b["style_href"] = f"../style/{b['style']}/index.html" if st else ""
        b["style_name"] = st["names"]["name"] if st else ""

    # The page opens on the recipe as its source has it — heat and sweetness at 1.0 — so the
    # first thing a reader sees is the cited proportions, and the dials move away from them.
    DEFAULTS = {"base": builder["bases"][0]["key"], "heat": "medium", "sweet": "sweet", "batch": "cup"}

    def dial(name, key, opts):
        return (f'<div class="dial"><b>{E(name)}</b><div class="opts" data-dial="{key}">'
                + "".join(f'<button type="button" data-v="{E(o["key"])}" '
                          f'aria-pressed="{"true" if o["key"] == DEFAULTS[key] else "false"}">{E(o["label"])}</button>'
                          for o in opts) + "</div></div>")

    RDEF = {"level": rub["levels"][1]["key"], "meat": "twenty", "heat": "medium"}
    SDEF = {"kind": dip["kinds"][0]["key"], "size": "cup", "sweet": "some", "heat": "some"}

    def sdial(name, key, opts):
        return (f'<div class="dial"><b>{E(name)}</b><div class="opts" data-dial="{key}">'
                + "".join(f'<button type="button" data-v="{E(o["key"])}" '
                          f'aria-pressed="{"true" if o["key"] == SDEF[key] else "false"}">{E(o["label"])}</button>'
                          for o in opts) + "</div></div>")

    def rdial(name, key, opts):
        return (f'<div class="dial"><b>{E(name)}</b><div class="opts" data-dial="{key}">'
                + "".join(f'<button type="button" data-v="{E(o["key"])}" '
                          f'aria-pressed="{"true" if o["key"] == RDEF[key] else "false"}">{E(o["label"])}</button>'
                          for o in opts) + "</div></div>")

    body = f"""
<h1><span class="kind">Wing Country</span>Make your own</h1>
<p class="lede">A sauce, a rub, or the cup beside the basket. Where a real recipe exists, it&#8217;s named. Where it
doesn&#8217;t, we say the proportions are ours.</p>

<div class="tabs" role="tablist">
  <button type="button" role="tab" data-panel="sauce" aria-selected="true">Sauce</button>
  <button type="button" role="tab" data-panel="rub" aria-selected="false">Rub</button>
  <button type="button" role="tab" data-panel="dip" aria-selected="false">Dip</button>
</div>

<section class="panel" id="panel-sauce">
<div class="dials">
  {dial("Style", "base", [{"key": b["key"], "label": b["name"]} for b in builder["bases"]])}
  {dial("Heat", "heat", builder["heats"])}
  {dial("Sweetness", "sweet", builder["sweets"])}
  {dial("How much", "batch", builder["batches"])}
</div>

<div class="recipe" id="out"></div>

</section>

<section class="panel" id="panel-rub" hidden>
<p class="carolina-note">{E(rub["house_note"])}</p>
<div class="dials">
  {rdial("How far out", "level", [{"key": l["key"], "label": l["name"]} for l in rub["levels"]])}
  {rdial("How many wings", "meat", [{"key": m["key"], "label": m["label"]} for m in rub["meats"]])}
  {rdial("Heat", "heat", rub["heats"])}
</div>
<div class="recipe" id="rubout"></div>
<p class="legend">Amounts per pound are this project's rule of thumb, not a kitchen's measurement — the proportions
inside each level are the cited thing. Ten pieces is taken as a pound.</p>
</section>

<section class="panel" id="panel-dip" hidden>
<p class="carolina-note">{E(dip["house_note"])}</p>
<div class="dials">
  {sdial("Which dip", "kind", [{"key": k["key"], "label": k["name"]} for k in dip["kinds"]])}
  {sdial("How much", "size", [{"key": z["key"], "label": z["label"]} for z in dip["sizes"]])}
  {sdial("Sweetness", "sweet", dip["sweets"])}
  {sdial("Heat", "heat", dip["heats"])}
</div>
<div class="recipe" id="slawout"></div>
<p class="legend">Quantities scale off the finished cup. Three of the four keep a Wikibooks recipe's own proportions
under CC BY-SA; the fourth says it is ours.</p>
</section>

<p class="legend">Sugar is worked out from the quantities on screen: {builder["sugar_g_per_tbsp"]["sugar"]} g of sugar in a
tablespoon of sugar, {builder["sugar_g_per_tbsp"]["honey"]} g in honey, {builder["sugar_g_per_tbsp"]["molasses"]} g in molasses,
{builder["sugar_g_per_tbsp"]["ketchup"]} g in ketchup. The bottles it is drawn against were read off their own labels for
<a href="../sauce/index.html">the sauce page</a>. A cayenne-and-butter sauce lands at nothing, and a honey one lands near
the top — same wing, two different foods.</p>

<script>
(function(){{
var B={esc_js(builder)}, BOTTLES={esc_js(bottles)};
var pick={{base:B.bases[0].key, heat:"medium", sweet:"sweet", batch:"cup"}};
function esc(s){{return String(s==null?"":s).replace(/[&<>"]/g,function(c){{return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]}})}}
var FRAC=[[1,"1"],[0.75,"¾"],[0.6667,"⅔"],[0.5,"½"],[0.3333,"⅓"],[0.25,"¼"],[0.125,"⅛"]];
function nice(tbsp){{
  /* the kitchen unit a cook would actually reach for */
  if(tbsp<=0) return null;
  var p=function(v,w){{return frac(v)+" "+w+(v>1.02?"s":"")}};
  if(tbsp>=16) return p(tbsp/16,"cup");
  if(tbsp>=1) return p(tbsp,"tablespoon");
  return p(tbsp*3,"teaspoon");
}}
function frac(v){{
  var whole=Math.floor(v+1e-9), rem=v-whole, best="", bd=9;
  for(var i=0;i<FRAC.length;i++){{var d=Math.abs(rem-FRAC[i][0]); if(d<bd){{bd=d;best=FRAC[i][1];}}}}
  if(rem<0.06) return String(whole||"0");
  /* a kitchen has no 0.58 of a spoon: snap to the nearest named fraction unless it is
     genuinely far from all of them */
  if(bd>0.1&&whole===0) return (Math.round(v*100)/100).toString();
  if(best==="1"){{whole+=1;best="";}}
  return (whole?whole+(best?" ":""):"")+best;
}}
function base(){{return B.bases.filter(function(b){{return b.key===pick.base}})[0]}}
function mult(list,key){{var m=list.filter(function(x){{return x.key===key}})[0]; return m?m.mult:1}}
function compute(){{
  var b=base(), tbsp=B.batches.filter(function(x){{return x.key===pick.batch}})[0].tbsp;
  var hm=mult(B.heats,pick.heat), sm=mult(B.sweets,pick.sweet);
  var rows=[], vol=0, sugar=0;
  b.ingredients.forEach(function(ing){{
    var f=ing.per_tbsp;
    if(ing.dial==="heat") f*=hm;
    if(ing.dial==="sweet") f*=sm;
    var q=f*tbsp;
    vol+=q;
    if(ing.sugar) sugar+=q*B.sugar_g_per_tbsp[ing.sugar];
    rows.push({{name:ing.name, q:q, hint:ing.unit_hint||""}});
  }});
  return {{b:b, rows:rows, vol:vol, sugar:vol>0?sugar/vol:0, tbsp:tbsp}};
}}
function scale(g){{
  /* the same 0 to 12.6 scale the sauce page uses */
  var w=420, x0=10, x1=w-10, pos=function(v){{return x0+(x1-x0)*Math.min(v/12.6,1)}};
  var o='<svg viewBox="0 0 '+w+' 64" role="img" aria-label="Where this sauce sits for sugar against the bottles measured for this site">';
  o+='<rect x="'+x0+'" y="26" width="'+(x1-x0)+'" height="8" rx="4" fill="var(--chip)"/>';
  BOTTLES.forEach(function(bt){{ o+='<circle cx="'+pos(bt.g).toFixed(1)+'" cy="30" r="3.4" fill="var(--mute)" opacity=".65"><title>'+esc(bt.n)+' — '+bt.g+' g</title></circle>'; }});
  o+='<circle cx="'+pos(g).toFixed(1)+'" cy="30" r="11" fill="var(--sauce)" opacity=".25"/>';
  o+='<circle cx="'+pos(g).toFixed(1)+'" cy="30" r="7" fill="var(--sauce)" stroke="var(--panel)" stroke-width="2"/>';
  o+='<text x="'+x0+'" y="56" fill="var(--mute)" style="font:600 11px var(--ui,sans-serif)">0 g</text>';
  o+='<text x="'+x1+'" y="56" text-anchor="end" fill="var(--mute)" style="font:600 11px var(--ui,sans-serif)">12.6 g — a spoonful of sugar</text>';
  return o+'</svg>';
}}
function gap(g,key){{
  /* the distance between what you just built and what the shelf sells, which is nearly
     all sugar — the site's own measurement, not an opinion about either one */
  var mine=BOTTLES.filter(function(b){{return b.b===key}}).map(function(b){{return b.g}}).sort(function(a,c){{return a-c}});
  if(mine.length<2) return "";
  var med=mine[Math.floor(mine.length/2)];
  var d=med-g;
  if(Math.abs(d)<0.6) return '<p class="nearby">That is about where the bottles of this kind sit — a median of '+med+' g.</p>';
  if(d>0) return '<p class="nearby">A bottle of this kind carries about <b>'+med+' g</b>, so the shelf is '+
    (d/Math.max(g,0.1)>=2?'several times':'a good deal')+' sweeter than this. Closing that gap means adding sugar until it is '+
    'roughly a quarter of the jar by weight, which is what those labels describe.</p>';
  return '<p class="nearby">That is sweeter than the bottles of this kind, which sit around '+med+' g.</p>';
}}function render(){{
  var r=compute(), b=r.b, a=b.anchor;
  var heat=B.heats.filter(function(x){{return x.key===pick.heat}})[0].label.toLowerCase();
  var sweet=B.sweets.filter(function(x){{return x.key===pick.sweet}})[0].label.toLowerCase();
  var batch=B.batches.filter(function(x){{return x.key===pick.batch}})[0].label;
  var ing=r.rows.map(function(x){{
    var q=nice(x.q);
    return '<li class="'+(q?'':'zero')+'"><span class="q">'+esc(q||'')+'</span><span>'+esc(x.name)+
      (x.hint?' <span class="mute">('+esc(x.hint)+')</span>':'')+'</span></li>';
  }}).join("");
  var near=BOTTLES.filter(function(bt){{return bt.b===b.key}})
      .sort(function(p,q){{return Math.abs(p.g-r.sugar)-Math.abs(q.g-r.sugar)}}).slice(0,3);
  var prov;
  if(a.kind==="recipe") prov='Built on <b>'+esc(a.title)+'</b>'+(a.year?', '+a.year:'')+', '+esc(a.publisher)+
      ' — '+esc(a.license)+(a.url?' · <a href="'+esc(a.url)+'" rel="noopener">the recipe</a>':'')+'. '+esc(a.note||'');
  else if(a.kind==="ancestor") prov='Descends from <b>'+esc(a.title)+'</b>, '+esc(a.publisher)+' '+(a.year||'')+
      ' ('+esc(a.license)+'). '+esc(a.note||'');
  else prov='<b>These proportions are this project\\'s own.</b> '+esc(a.note||'');
  document.getElementById("out").innerHTML=
    '<h3>'+esc(b.name)+', '+esc(heat)+', '+esc(sweet)+' — '+esc(batch)+'</h3>'+
    '<p class="says">'+esc(b.says)+' · '+esc(b.region)+'</p>'+
    '<ul>'+ing+'</ul>'+
    '<h4>How</h4><ol>'+b.method.map(function(m){{return '<li>'+esc(m)+'</li>'}}).join("")+'</ol>'+
    '<div class="sugarline"><b>'+r.sugar.toFixed(1)+' g</b><span class="mute">of sugar in a tablespoon of it</span></div>'+
    scale(r.sugar)+
    gap(r.sugar,b.key)+
    (near.length?'<p class="nearby">Nearest bottles on the shelf: '+near.map(function(x){{return esc(x.n)+' ('+x.g+' g)'}}).join(' · ')+'</p>':'')+
    '<div class="mk-actions"><button type="button" class="btn" id="copy">Copy the recipe</button>'+
    (b.href?'<a class="btn ghost" href="'+b.href+'">About this sauce</a>':'')+
    (b.style_href?'<a class="btn ghost" href="'+b.style_href+'">'+esc(b.style_name)+'</a>':'')+'</div>'+
    '<p class="prov">'+prov+' Method '+(b.method_tier==="cited"?'as published':b.method_tier==="tradition"?'as the tradition has it':'is ours')+'.</p>';
  document.getElementById("copy").addEventListener("click",function(){{
    var txt=b.name+' sauce — '+heat+', '+sweet+', '+batch+'\\n\\n'+
      r.rows.filter(function(x){{return nice(x.q)}}).map(function(x){{return nice(x.q)+'  '+x.name}}).join('\\n')+
      '\\n\\n'+b.method.join('\\n')+'\\n\\n'+r.sugar.toFixed(1)+' g sugar per tablespoon.\\n'+
      'From Wing Country — {site_url}/make/';
    (navigator.clipboard?navigator.clipboard.writeText(txt):Promise.reject()).then(function(){{
      document.getElementById("copy").textContent="Copied";
      setTimeout(function(){{document.getElementById("copy").textContent="Copy the recipe"}},1600);}},function(){{}});
  }});
}}
document.querySelector("#panel-sauce .dials").addEventListener("click",function(e){{
  var btn=e.target.closest("button[data-v]"); if(!btn)return;
  var group=btn.closest("[data-dial]"), k=group.dataset.dial;
  pick[k]=btn.dataset.v;
  [].forEach.call(group.querySelectorAll("button"),function(x){{x.setAttribute("aria-pressed",x===btn?"true":"false")}});
  render();
}});
render();
}})();

/* ------------------------------------------------------------------ the rub */
(function(){{
var R={esc_js(rub)}, pick={{level:R.levels[1].key, meat:"twenty", heat:"medium"}};
function esc(s){{return String(s==null?"":s).replace(/[&<>"]/g,function(c){{return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]}})}}
var FR=[[1,"1"],[0.75,"¾"],[0.6667,"⅔"],[0.5,"½"],[0.3333,"⅓"],[0.25,"¼"],[0.125,"⅛"]];
function frac(v){{var w=Math.floor(v+1e-9),r=v-w,b="",bd=9;
  for(var i=0;i<FR.length;i++){{var d=Math.abs(r-FR[i][0]); if(d<bd){{bd=d;b=FR[i][1];}}}}
  if(r<0.06)return String(w||"0");
  if(bd>0.08&&w===0)return (Math.round(v*100)/100).toString();
  if(b==="1"){{w+=1;b="";}}
  return (w?w+(b?" ":""):"")+b;}}
function nice(tbsp){{if(tbsp<=0)return null;
  var p=function(v,wd){{return frac(v)+" "+wd+(v>1.02?"s":"")}};
  if(tbsp>=16)return p(tbsp/16,"cup");
  if(tbsp>=1)return p(tbsp,"tablespoon");
  return p(tbsp*3,"teaspoon");}}
function rate(tbspPerLb){{
  /* under a tablespoon reads better as teaspoons, which is where every level but the last sits */
  if(tbspPerLb>=1) return frac(tbspPerLb)+' tablespoon'+(tbspPerLb>1.02?'s':'');
  var t=tbspPerLb*3; return frac(t)+' teaspoon'+(t>1.02?'s':'');
}}
function lvl(){{return R.levels.filter(function(x){{return x.key===pick.level}})[0]}}
function render(){{
  var L=lvl(), M=R.meats.filter(function(x){{return x.key===pick.meat}})[0];
  var hm=R.heats.filter(function(x){{return x.key===pick.heat}})[0];
  var total=L.tbsp_per_lb*M.lb, rows=[], sum=0;
  for(var k in L.parts){{
    var f=L.parts[k];
    if(R.heat_ingredients.indexOf(k)>=0) f*=hm.mult;
    rows.push({{name:k, q:f*total}}); sum+=f*total;
  }}
  var a=L.anchor, prov;
  if(a.kind==="recipe") prov='<b>'+esc(a.title)+'</b>, '+esc(a.publisher)+' — '+esc(a.license)+
     (a.url?' · <a href="'+esc(a.url)+'" rel="noopener">the recipe</a>':'')+'. '+esc(a.note);
  else if(a.kind==="named") prov='<b>'+esc(a.title)+'</b>, from '+esc(a.publisher)+
     (a.url?' · <a href="'+esc(a.url)+'" rel="noopener">the article</a>':'')+'. '+esc(a.note);
  else prov=esc(a.note);
  document.getElementById("rubout").innerHTML=
    '<h3>'+esc(L.name)+' — for '+esc(M.label.toLowerCase())+'</h3>'+
    '<p class="says">'+esc(L.says)+'</p>'+
    '<p class="per">'+esc(M.label)+' is taken as <b>'+M.lb+' lb</b> ('+esc(M.note)+'), at '+
      rate(L.tbsp_per_lb)+' of rub to the pound.</p>'+
    '<ul>'+rows.map(function(x){{var q=nice(x.q);
      return '<li class="'+(q?'':'zero')+'"><span class="q">'+esc(q||'')+'</span><span>'+esc(x.name)+'</span></li>';}}).join("")+'</ul>'+
    '<p class="per">About '+esc(nice(sum)||"nothing")+' of rub in all.</p>'+
    (L.when?'<h4>When</h4><ol>'+L.when.map(function(m){{return '<li>'+esc(m)+'</li>'}}).join("")+'</ol>':'')+
    '<div class="mk-actions"><button type="button" class="btn" id="rubcopy">Copy the rub</button>'+
    '<a class="btn ghost" href="../wing/index.html">Which part of the bird</a>'+
    '<a class="btn ghost" href="../fry/the-toss/index.html">The toss</a></div>'+
    '<p class="prov">'+prov+'</p>';
  document.getElementById("rubcopy").addEventListener("click",function(){{
    var txt=L.name+' — for '+M.label.toLowerCase()+' ('+M.lb+' lb)\\n\\n'+
      rows.filter(function(x){{return nice(x.q)}}).map(function(x){{return nice(x.q)+'  '+x.name}}).join('\\n')+
      '\\n\\nFrom Wing Country — {site_url}/make/';
    (navigator.clipboard?navigator.clipboard.writeText(txt):Promise.reject()).then(function(){{
      var b=document.getElementById("rubcopy"); b.textContent="Copied";
      setTimeout(function(){{b.textContent="Copy the rub"}},1600);}},function(){{}});
  }});
}}
document.querySelector("#panel-rub .dials").addEventListener("click",function(e){{
  var btn=e.target.closest("button[data-v]"); if(!btn)return;
  var g=btn.closest("[data-dial]"); pick[g.dataset.dial]=btn.dataset.v;
  [].forEach.call(g.querySelectorAll("button"),function(x){{x.setAttribute("aria-pressed",x===btn?"true":"false")}});
  render();
}});
render();
}})();

/* ------------------------------------------------------------------ the dip */
(function(){{
var S={esc_js(dip)}, pick={{kind:S.kinds[0].key, size:"cup", sweet:"some", heat:"some"}};
function esc(s){{return String(s==null?"":s).replace(/[&<>"]/g,function(c){{return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]}})}}
var FS=[[1,"1"],[0.75,"¾"],[0.6667,"⅔"],[0.5,"½"],[0.3333,"⅓"],[0.25,"¼"],[0.125,"⅛"]];
function frac(v){{var w=Math.floor(v+1e-9),r=v-w,b="",bd=9;
  for(var i=0;i<FS.length;i++){{var d=Math.abs(r-FS[i][0]); if(d<bd){{bd=d;b=FS[i][1];}}}}
  if(r<0.06)return String(w||"0");
  if(bd>0.08&&w===0)return (Math.round(v*100)/100).toString();
  if(b==="1"){{w+=1;b="";}}
  return (w?w+(b?" ":""):"")+b;}}
function amount(q,unit){{
  /* cups fall back to tablespoons and spoons to each other, so nothing reads as 0.06 cup */
  if(q<=0)return null;
  var plural=function(v,w){{return frac(v)+" "+w+(v>1.02?"s":"")}};
  if(unit==="cup"){{ if(q<0.25) return plural(q*16,"tablespoon"); return plural(q,"cup"); }}
  if(unit==="tbsp"){{ if(q<1) return plural(q*3,"teaspoon"); return plural(q,"tablespoon"); }}
  if(unit==="tsp"){{ if(q>=3) return plural(q/3,"tablespoon"); return plural(q,"teaspoon"); }}
  if(unit==="egg"){{ return frac(q); }}
  return plural(q,unit);
}}
function kind(){{return S.kinds.filter(function(x){{return x.key===pick.kind}})[0]}}
function render(){{
  var K=kind(), Z=S.sizes.filter(function(x){{return x.key===pick.size}})[0];
  var sw=S.sweets.filter(function(x){{return x.key===pick.sweet}})[0].mult;
  var ht=S.heats.filter(function(x){{return x.key===pick.heat}})[0].mult;
  var rows=K.per_cup.map(function(ing){{
    var q=ing.q*Z.cups;
    if(ing.dial==="sweet") q*=sw;
    if(ing.dial==="heat") q*=ht;
    return {{name:ing.name, txt:amount(q,ing.unit), opt:!!ing.optional}};
  }});
  var a=K.anchor, prov;
  if(a.kind==="recipe") prov='<b>'+esc(a.title)+'</b>, '+esc(a.publisher)+' '+(a.year||'')+' ('+esc(a.license)+'). '+esc(a.note);
  else prov='<b>These proportions are ours.</b> '+esc(a.note);
  document.getElementById("slawout").innerHTML=
    '<h3>'+esc(K.name)+' — '+esc(Z.label.toLowerCase())+'</h3>'+
    '<p class="says">'+esc(K.says)+' · '+esc(K.region)+'</p>'+
    '<p class="per">Makes about <b>'+Z.cups+' cup'+(Z.cups>1?'s':'')+'</b>.</p>'+
    '<ul>'+
    rows.map(function(x){{
      return '<li class="'+(x.txt?'':'zero')+'"><span class="q">'+esc(x.txt||'')+'</span><span>'+esc(x.name)+
        (x.opt?' <span class="mute">(optional)</span>':'')+'</span></li>';}}).join("")+'</ul>'+
    '<h4>How</h4><ol>'+K.steps.map(function(m){{return '<li>'+esc(m)+'</li>'}}).join("")+'</ol>'+
    (K.swap?'<p class="per"><b>Or:</b> '+esc(K.swap)+'</p>':'')+
    '<div class="mk-actions"><button type="button" class="btn" id="slawcopy">Copy the dip</button>'+
    '<a class="btn ghost" href="../sauce/'+esc(K.dish)+'/index.html">About this dip</a></div>'+
    '<p class="prov">'+prov+(K.verbatim?' Steps quoted from the receipt.':' Steps are ours.')+'</p>';
  document.getElementById("slawcopy").addEventListener("click",function(){{
    var txt=K.name+' — '+Z.label.toLowerCase()+'\\n\\n'+
      rows.filter(function(x){{return x.txt}}).map(function(x){{return x.txt+'  '+x.name}}).join('\\n')+
      '\\n\\n'+K.steps.join('\\n')+'\\n\\nFrom Wing Country — {site_url}/make/';
    (navigator.clipboard?navigator.clipboard.writeText(txt):Promise.reject()).then(function(){{
      var b=document.getElementById("slawcopy"); b.textContent="Copied";
      setTimeout(function(){{b.textContent="Copy the dip"}},1600);}},function(){{}});
  }});
}}
document.querySelector("#panel-dip .dials").addEventListener("click",function(e){{
  var btn=e.target.closest("button[data-v]"); if(!btn)return;
  var g=btn.closest("[data-dial]"); pick[g.dataset.dial]=btn.dataset.v;
  [].forEach.call(g.querySelectorAll("button"),function(x){{x.setAttribute("aria-pressed",x===btn?"true":"false")}});
  render();
}});
render();
}})();

/* ------------------------------------------------------------------ the tabs */
(function(){{
var tabs=document.querySelector(".tabs");
tabs.addEventListener("click",function(e){{
  var b=e.target.closest("button[data-panel]"); if(!b)return;
  [].forEach.call(tabs.querySelectorAll("button"),function(x){{
    var on=x===b; x.setAttribute("aria-selected",on?"true":"false");
    document.getElementById("panel-"+x.dataset.panel).hidden=!on;
  }});
}});
}})();
</script>
"""
    return page("Make your own — Wing Country", body, 1,
                "Build a wing sauce by style and taste, a rub from nothing at all out to a full barbecue one, or the dip beside the basket. Every proportion says whether it came from a published recipe or from this project.",
                None, f"{site_url}/make/", extra_head=f"<style>{MAKE_CSS}{MAKE_TABS_CSS}{CHART_CSS}</style>", card="make",
                og_alt="Make a wing sauce, a rub or a dip")
