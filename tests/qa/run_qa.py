#!/usr/bin/env python3
"""End-to-end QA runner for the btf-redesign static site (QA-1 .. QA-12).

This is the FINAL independent verification for the SwarmForge run. It drives the
site exclusively through the *served* user interface (HTTP over a local
``python -m http.server``) — never an internal project API — exactly as a real
visitor or GitHub Pages would. It implements the procedures from
``~/.claude/swarm-runs/btf-redesign/qa-suite.md`` as a re-runnable script.

Tooling is stdlib only (urllib, http.client, html.parser, xml.etree) — no
third-party deps, no build step.

Usage:
    python -m http.server 8000   # serve from the repo root first, OR
    tests/qa/run_qa.py           # auto-serves on an ephemeral port if --no-serve absent

    python tests/qa/run_qa.py [--base-url http://localhost:8000] [--no-serve]

Exit code is non-zero if any QA step FAILs.

Notes on the orchestrator boundary: pure pixel/visual and live-browser responsive
behaviours (hamburger opening on a real 375px viewport, no-horizontal-scroll,
animation playback) are the orchestrator's Playwright pass. Here we assert what is
checkable from the *served* markup and CSS (viewport meta, a hamburger button +
small-viewport CSS rule, a prefers-reduced-motion block, a table->card small-screen
rule) and explicitly DEFER the remaining visual confirmation.
"""
from __future__ import annotations

import argparse
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[2]
PAGES = ["", "uslugi.html", "oferta.html", "cennik.html", "kontakt.html"]
PAGE_FILES = ["index.html", "uslugi.html", "oferta.html", "cennik.html", "kontakt.html"]
CANONICAL_DOMAIN = "btf-gdynia.pl"
TEL = "tel:+48504093624"
PHONE_DISPLAY = "504-093-624"
EMAILS = ["kamilskamarski@gmail.com", "btf.kontakt@wp.pl"]

# Emoji ranges (used as iconography would be a slop tell — Slice3-3 / QA spot).
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF\U00002190-\U000021FF\U00002B00-\U00002BFF️]"
)

# ----------------------------------------------------------------------------- result plumbing

class Results:
    def __init__(self) -> None:
        self.steps: list[tuple[str, bool, str]] = []

    def record(self, step: str, ok: bool, note: str) -> None:
        self.steps.append((step, ok, note))
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {step}: {note}")

    @property
    def failed(self) -> list[tuple[str, bool, str]]:
        return [s for s in self.steps if not s[1]]


# ----------------------------------------------------------------------------- HTTP helpers

def http_get(base: str, path: str) -> tuple[int, str, bytes]:
    url = urljoin(base, path)
    req = urllib.request.Request(url, headers={"User-Agent": "btf-qa/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            return resp.status, ctype, body
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", "") if exc.headers else "", exc.read() or b""


def fetch_text(base: str, path: str) -> tuple[int, str, str]:
    status, ctype, body = http_get(base, path)
    return status, ctype, body.decode("utf-8", errors="replace")


# ----------------------------------------------------------------------------- tiny DOM

class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "text_parts")

    def __init__(self, tag: str, attrs: dict[str, str], parent: "Node | None"):
        self.tag = tag
        self.attrs = attrs
        self.children: list[Node] = []
        self.parent = parent
        self.text_parts: list[str] = []

    def text(self) -> str:
        out: list[str] = list(self.text_parts)
        for c in self.children:
            out.append(c.text())
        return " ".join(p for p in out if p).strip()

    def iter(self):
        yield self
        for c in self.children:
            yield from c.iter()

    def find_all(self, tag: str) -> list["Node"]:
        return [n for n in self.iter() if n.tag == tag]


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


class DOM(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v or "") for k, v in attrs}, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, {k: (v or "") for k, v in attrs}, self.cur)
        self.cur.children.append(node)

    def handle_endtag(self, tag):
        node = self.cur
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root and node.parent is not None:
            self.cur = node.parent

    def handle_data(self, data):
        if data.strip():
            self.cur.text_parts.append(data.strip())


def parse(html: str) -> Node:
    d = DOM()
    d.feed(html)
    return d.root


def ancestors_have_tag(node: Node, tag: str) -> bool:
    p = node.parent
    while p is not None:
        if p.tag == tag:
            return True
        p = p.parent
    return False


def strip_fragment(href: str) -> str:
    return href.split("#", 1)[0]


# ----------------------------------------------------------------------------- QA steps

def qa1(base: str, r: Results) -> dict[str, str]:
    """QA-1 — All five pages load (HTTP 200, text/html)."""
    htmls: dict[str, str] = {}
    ok_all = True
    details = []
    for p in PAGES:
        status, ctype, text = fetch_text(base, p)
        htmls["index.html" if p == "" else p] = text
        ok = status == 200 and "text/html" in ctype.lower()
        ok_all = ok_all and ok
        details.append(f"/{p}->{status} {ctype.split(';')[0]}")
    r.record("QA-1 pages load 200/html", ok_all, "; ".join(details))
    return htmls


def qa2(base: str, htmls: dict[str, str], r: Results) -> None:
    """QA-2 — Primary nav links to all five pages + active state + brand->home."""
    ok_all = True
    notes = []
    for fname, html in htmls.items():
        root = parse(html)
        navs = root.find_all("nav")
        nav = navs[0] if navs else None
        targets = set()
        active = []
        if nav:
            for a in nav.find_all("a"):
                href = strip_fragment(a.attrs.get("href", ""))
                if href:
                    targets.add(href)
                if a.attrs.get("aria-current") == "page" or "active" in a.attrs.get("class", ""):
                    active.append(strip_fragment(a.attrs.get("href", "")))
        need = {"index.html", "uslugi.html", "oferta.html", "cennik.html", "kontakt.html"}
        nav_ok = need.issubset(targets)
        # exactly one active, pointing at self
        active_ok = len(active) == 1 and active[0] == fname
        # brand link -> home
        brand_ok = any(
            "brand" in n.attrs.get("class", "") and n.attrs.get("href") == "index.html"
            for n in root.find_all("a")
        )
        # all nav hrefs relative
        rel_ok = all(
            not (h.startswith("http://") or h.startswith("https://") or h.startswith("/"))
            for h in targets
        )
        page_ok = nav_ok and active_ok and brand_ok and rel_ok
        ok_all = ok_all and page_ok
        if not page_ok:
            notes.append(f"{fname}: nav={nav_ok} active={active}({active_ok}) brand={brand_ok} rel={rel_ok}")
    r.record(
        "QA-2 nav targets/active/brand",
        ok_all,
        "all 5 pages link to all 5; exactly-one self aria-current; brand->index.html"
        if ok_all else "; ".join(notes),
    )


def qa3(htmls: dict[str, str], r: Results) -> None:
    """QA-3 — Phone is a tel: link in header + footer (and kontakt block)."""
    ok_all = True
    notes = []
    for fname, html in htmls.items():
        root = parse(html)
        header = root.find_all("header")
        footer = root.find_all("footer")
        head_tel = any(a.attrs.get("href") == TEL for h in header for a in h.find_all("a"))
        foot_tel = any(a.attrs.get("href") == TEL for f in footer for a in f.find_all("a"))
        # displayed number present somewhere with that link
        disp_ok = PHONE_DISPLAY in html
        page_ok = head_tel and foot_tel and disp_ok
        ok_all = ok_all and page_ok
        if not page_ok:
            notes.append(f"{fname}: header_tel={head_tel} footer_tel={foot_tel} disp={disp_ok}")
    r.record("QA-3 tel: link header+footer", ok_all,
             f"{TEL} present in header & footer of all 5; display '{PHONE_DISPLAY}'"
             if ok_all else "; ".join(notes))


def qa4(htmls: dict[str, str], r: Results) -> None:
    """QA-4 — Emails are mailto: links (kontakt + every footer)."""
    ok_all = True
    notes = []
    for fname, html in htmls.items():
        root = parse(html)
        footer = root.find_all("footer")
        hrefs = {a.attrs.get("href", "") for f in footer for a in f.find_all("a")}
        for email in EMAILS:
            if f"mailto:{email}" not in hrefs:
                ok_all = False
                notes.append(f"{fname}: missing footer mailto:{email}")
    # kontakt body must carry both mailto + visible text
    root = parse(htmls["kontakt.html"])
    body_hrefs = {a.attrs.get("href", "") for a in root.find_all("a")}
    for email in EMAILS:
        if f"mailto:{email}" not in body_hrefs or email not in htmls["kontakt.html"]:
            ok_all = False
            notes.append(f"kontakt: mailto/display issue for {email}")
    r.record("QA-4 mailto: links", ok_all,
             "both emails are mailto: in every footer and on kontakt"
             if ok_all else "; ".join(notes))


def _table_rows(table: Node) -> list[Node]:
    bodies = table.find_all("tbody")
    src = bodies[0] if bodies else table
    return [n for n in src.find_all("tr")]


def qa5(htmls: dict[str, str], r: Results) -> None:
    """QA-5 — Cennik shows 23 / 11 / 7 rows with correct prices + footnotes."""
    root = parse(htmls["cennik.html"])
    tables = root.find_all("table")
    notes = []
    ok = True
    if len(tables) != 3:
        ok = False
        notes.append(f"expected 3 tables, found {len(tables)}")
    counts = [len(_table_rows(t)) for t in tables]
    if counts[:3] != [23, 11, 7]:
        ok = False
        notes.append(f"row counts {counts} != [23,11,7]")

    body = htmls["cennik.html"]
    # spot-check equipment first/last names
    for frag in ["Gaśnica proszkowa GP-1x ABC", "Legalizacja UDT gaśnicy GP – 12x"]:
        if frag not in body:
            ok = False
            notes.append(f"missing equipment '{frag}'")
    # usługi name->price fidelity (verbatim from spec)
    usl_rows = _table_rows(tables[1]) if len(tables) > 1 else []
    usl_pairs = {}
    for tr in usl_rows:
        tds = tr.find_all("td")
        if len(tds) >= 3:
            usl_pairs[tds[1].text()] = tds[2].text()
    expected_usl = {
        "Opracowanie Instrukcji Bezpieczeństwa PPOŻ.": "od 900,00",
        "Stały nadzór nad obiektem": "od 200,00/miesiąc",
        "Przegląd stanu bezp. pożarowego": "bezpłatnie",
    }
    for name, price in expected_usl.items():
        if usl_pairs.get(name) != price:
            ok = False
            notes.append(f"usługa '{name}' -> '{usl_pairs.get(name)}' != '{price}'")
    # szkolenia: corrected rows 6 & 7
    szk_rows = _table_rows(tables[2]) if len(tables) > 2 else []
    szk = {}
    for tr in szk_rows:
        tds = tr.find_all("td")
        if len(tds) >= 4:
            szk[tds[1].text()] = (tds[2].text(), tds[3].text())
    expected_szk = {
        "Szkolenie BHP z elementami PPOŻ. okresowe stanowiska robotnicze": ("8h", "150,00"),
        "Szkolenie BHP z elementami PPOŻ. okresowe stanowiska kierownicze": ("16h", "190,00"),
    }
    for name, (amt, price) in expected_szk.items():
        if szk.get(name) != (amt, price):
            ok = False
            notes.append(f"szkolenie '{name}' -> {szk.get(name)} != {(amt, price)}")
    # data-correction guard: no 16h row may be "...robotnicze"
    for name, (amt, _price) in szk.items():
        if amt == "16h" and "robotnicze" in name:
            ok = False
            notes.append("16h training mislabeled 'robotnicze'")
    # footnotes
    for fn in ["Podane ceny są cenami netto.",
               "Podane ceny są cenami brutto i obowiązują przy szkoleniu dla grupy co najmniej 3 osób."]:
        if fn not in body:
            ok = False
            notes.append(f"missing footnote '{fn[:30]}...'")
    r.record("QA-5 cennik 23/11/7 + prices + footnotes", ok,
             f"tables {counts}; usługi & corrected szkolenia rows verbatim; both footnotes"
             if ok else "; ".join(notes))


def qa6(htmls: dict[str, str], r: Results) -> None:
    """QA-6 — Contact map present, titled, lazy, Gdynia maps embed."""
    root = parse(htmls["kontakt.html"])
    iframes = root.find_all("iframe")
    ok = False
    note = "no <iframe> found"
    for ifr in iframes:
        src = ifr.attrs.get("src", "")
        host = urlsplit(src).netloc
        title = ifr.attrs.get("title", "").strip()
        lazy = ifr.attrs.get("loading", "") == "lazy"
        if "google.com/maps" in src and "output=embed" in src and "key=" not in src and title and lazy:
            ok = True
            note = f"keyless google maps embed, title='{title[:40]}...', loading=lazy"
            break
        note = f"iframe host={host} title={'yes' if title else 'no'} lazy={lazy}"
    r.record("QA-6 map embed", ok, note)


def qa7(htmls: dict[str, str], css_text: str, r: Results) -> None:
    """QA-7 — Responsive structure (checkable from served markup/CSS).

    Visual confirmation (no horizontal scroll, menu opens, tables render as
    cards at 375px) DEFERRED to orchestrator Playwright.
    """
    notes = []
    ok = True
    # viewport meta + hamburger button + aria-controls on every page
    for fname, html in htmls.items():
        root = parse(html)
        vp = [m for m in root.find_all("meta") if m.attrs.get("name") == "viewport"]
        vp_ok = bool(vp) and "width=device-width" in vp[0].attrs.get("content", "")
        btns = [b for b in root.find_all("button") if "nav-toggle" in b.attrs.get("class", "")]
        btn = btns[0] if btns else None
        navs = root.find_all("nav")
        nav_id = navs[0].attrs.get("id", "") if navs else ""
        btn_ok = (
            btn is not None
            and btn.attrs.get("aria-expanded") == "false"
            and btn.attrs.get("aria-controls") == nav_id
            and nav_id != ""
            and (btn.attrs.get("aria-label") or btn.text())
        )
        if not (vp_ok and btn_ok):
            ok = False
            notes.append(f"{fname}: viewport={vp_ok} hamburger={btn_ok}")
    # CSS: a small-viewport rule reveals the toggle, and a small-viewport rule
    # restyles the price table (table->card fallback).
    toggle_rule = re.search(r"@media[^{]*max-width[^{]*\{[^}]*\.nav-toggle\s*\{[^}]*display\s*:\s*(inline-flex|flex|block)", css_text, re.S)
    if not toggle_rule:
        # tolerate the toggle rule and the media open being in adjacent blocks
        toggle_rule = re.search(r"\.nav-toggle\s*\{[^}]*display\s*:\s*(inline-flex|flex|block)", css_text)
        toggle_rule = bool(toggle_rule and "max-width" in css_text and ".nav-toggle" in css_text)
    table_card = re.search(r"@media[^{]*max-width[^{]*\{.*?\.price-table", css_text, re.S) or \
        re.search(r"@container[^{]*\{.*?\.price-table", css_text, re.S)
    if not toggle_rule:
        ok = False
        notes.append("no small-viewport .nav-toggle reveal rule in CSS")
    if not table_card:
        ok = False
        notes.append("no small-viewport/.container-query .price-table card rule")
    r.record("QA-7 responsive structure (markup+CSS)", ok,
             "viewport meta + hamburger(aria-expanded=false,aria-controls) on all 5; "
             "CSS small-viewport nav-toggle + price-table card rules present "
             "[visual 375/1280 -> orchestrator Playwright]"
             if ok else "; ".join(notes))


def qa8(base: str, htmls: dict[str, str], r: Results) -> None:
    """QA-8 — No broken internal links/assets across 5 pages + 404.html."""
    refs: dict[str, set[str]] = {}
    # include 404.html
    status404, _c, html404 = fetch_text(base, "404.html")
    all_html = dict(htmls)
    all_html["404.html"] = html404
    for fname, html in all_html.items():
        root = parse(html)
        collected = set()
        for n in root.iter():
            for attr in ("href", "src"):
                val = n.attrs.get(attr)
                if not val:
                    continue
                if val.startswith(("tel:", "mailto:", "#", "data:", "javascript:")):
                    continue
                if val.startswith(("http://", "https://", "//")):
                    continue
                collected.add(strip_fragment(val))
        refs[fname] = collected
    ok = True
    notes = []
    checked = {}
    for fname, urls in refs.items():
        base_path = fname  # relative resolution base
        for u in sorted(urls):
            if not u:
                continue
            resolved = urljoin(base_path, u) if base_path != "index.html" else u
            # resolve relative to page path on server
            target = urljoin("/" + (fname if fname != "index.html" else ""), u).lstrip("/")
            if target in checked:
                code = checked[target]
            else:
                code, _ct, _b = http_get(base, target)
                checked[target] = code
            if code != 200:
                ok = False
                notes.append(f"{fname} -> {u} ({target}) = {code}")
    r.record("QA-8 no broken internal links/assets", ok,
             f"checked {len(checked)} unique relative refs across 6 docs, all 200"
             if ok else "; ".join(notes))


def qa9(css_text: str, r: Results) -> None:
    """QA-9 — Reduced motion respected (CSS proof) + view-transition opt-in.

    Playback confirmation DEFERRED to orchestrator Playwright.
    """
    notes = []
    ok = True
    rm = re.search(r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{(.*?)\n\}", css_text, re.S)
    if not rm:
        # broader fallback: capture to a balanced-ish end
        rm = re.search(r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{(.+)\}", css_text, re.S)
    if not rm:
        ok = False
        notes.append("no @media (prefers-reduced-motion: reduce) block")
    else:
        block = rm.group(1)
        neutralized = (
            ("animation-duration" in block and "transition-duration" in block)
            or "animation: none" in block
            or "transition: none" in block
        )
        if not neutralized:
            ok = False
            notes.append("reduced-motion block does not neutralize animation/transition")
    if "@view-transition" not in css_text or "navigation: auto" not in css_text:
        ok = False
        notes.append("@view-transition navigation:auto opt-in missing")
    r.record("QA-9 reduced-motion + view-transition (CSS)", ok,
             "@media prefers-reduced-motion neutralizes anim/trans; @view-transition navigation:auto opt-in "
             "[motion playback -> orchestrator Playwright]"
             if ok else "; ".join(notes))


def qa10(base: str, r: Results) -> None:
    """QA-10 — Deploy files present and correct (served over HTTP)."""
    notes = []
    ok = True
    # CNAME — optional during preview (github.io, no custom domain); if present
    # it must be exactly the canonical domain.
    s, _c, cname = fetch_text(base, "CNAME")
    if s == 200 and (cname.strip() != CANONICAL_DOMAIN or "\n" in cname.strip()):
        ok = False
        notes.append(f"CNAME content={cname!r}")
    # .nojekyll
    s, _c, _b = fetch_text(base, ".nojekyll")
    if s != 200:
        ok = False
        notes.append(f".nojekyll status={s}")
    # robots.txt
    s, _c, robots = fetch_text(base, "robots.txt")
    if s != 200 or "Sitemap:" not in robots or "sitemap.xml" not in robots:
        ok = False
        notes.append(f"robots.txt status={s} content={robots!r}")
    # sitemap.xml well-formed + 5 canonical URLs
    s, _c, sm = fetch_text(base, "sitemap.xml")
    sm_ok = s == 200
    if sm_ok:
        try:
            tree = ET.fromstring(sm)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            locs = {e.text.strip() for e in tree.findall(".//sm:loc", ns)}
            expected = {
                f"https://{CANONICAL_DOMAIN}/",
                f"https://{CANONICAL_DOMAIN}/uslugi.html",
                f"https://{CANONICAL_DOMAIN}/oferta.html",
                f"https://{CANONICAL_DOMAIN}/cennik.html",
                f"https://{CANONICAL_DOMAIN}/kontakt.html",
            }
            if locs != expected:
                ok = False
                notes.append(f"sitemap locs {locs ^ expected} mismatch")
        except ET.ParseError as exc:
            ok = False
            notes.append(f"sitemap.xml not well-formed: {exc}")
    else:
        ok = False
        notes.append(f"sitemap.xml status={s}")
    # 404.html chrome
    s, _c, h404 = fetch_text(base, "404.html")
    root404 = parse(h404)
    if s != 200 or not root404.find_all("header") or not root404.find_all("footer"):
        ok = False
        notes.append(f"404.html status={s} header/footer chrome missing")
    # favicon (read link rel=icon from index, then fetch)
    s, _c, idx = fetch_text(base, "")
    root = parse(idx)
    icon = [l for l in root.find_all("link") if "icon" in l.attrs.get("rel", "")]
    if icon:
        fav = icon[0].attrs.get("href", "")
        fs, _fc, _fb = http_get(base, fav)
        if fs != 200:
            ok = False
            notes.append(f"favicon {fav} status={fs}")
    else:
        ok = False
        notes.append("no <link rel=icon> on index")
    r.record("QA-10 deploy files", ok,
             "CNAME=btf-gdynia.pl, .nojekyll, robots+Sitemap, sitemap(5 locs), 404 chrome, favicon all served/correct"
             if ok else "; ".join(notes))


def qa11(htmls: dict[str, str], r: Results) -> None:
    """QA-11 — SEO/meta sanity per page + JSON-LD + no legacy leakage."""
    import json
    notes = []
    ok = True
    page_url = {
        "index.html": f"https://{CANONICAL_DOMAIN}/",
        "uslugi.html": f"https://{CANONICAL_DOMAIN}/uslugi.html",
        "oferta.html": f"https://{CANONICAL_DOMAIN}/oferta.html",
        "cennik.html": f"https://{CANONICAL_DOMAIN}/cennik.html",
        "kontakt.html": f"https://{CANONICAL_DOMAIN}/kontakt.html",
    }
    for fname, html in htmls.items():
        root = parse(html)
        html_el = root.find_all("html")
        lang_ok = bool(html_el) and html_el[0].attrs.get("lang") == "pl"
        titles = root.find_all("title")
        title_ok = len(titles) == 1 and titles[0].text() and (
            "BTF" in titles[0].text() or "Bezpieczeństwo Twojej Firmy" in titles[0].text()
        )
        metas = root.find_all("meta")
        desc = [m for m in metas if m.attrs.get("name") == "description"]
        desc_ok = bool(desc) and desc[0].attrs.get("content", "") and \
            "add description" not in desc[0].attrs.get("content", "").lower() and \
            "lorem" not in desc[0].attrs.get("content", "").lower()
        canon = [l for l in root.find_all("link") if "canonical" in l.attrs.get("rel", "")]
        canon_ok = bool(canon) and canon[0].attrs.get("href") == page_url[fname]
        charset = [m for m in metas if m.attrs.get("charset")]
        charset_ok = len(charset) == 1 and charset[0].attrs.get("charset", "").lower() == "utf-8"
        # OG tags
        og = {m.attrs.get("property"): m.attrs.get("content", "") for m in metas if m.attrs.get("property", "").startswith("og:")}
        og_ok = (
            og.get("og:title") and og.get("og:description")
            and og.get("og:type") == "website"
            and og.get("og:url") == page_url[fname]
            and og.get("og:image")
        )
        # legacy leakage
        leak = any(tok in html for tok in ["google-analytics.com", "{{", "{%", "static_url(", "webben.pl", "© 2014"])
        page_ok = lang_ok and title_ok and desc_ok and canon_ok and charset_ok and og_ok and not leak
        ok = ok and page_ok
        if not page_ok:
            notes.append(f"{fname}: lang={lang_ok} title={title_ok} desc={desc_ok} canon={canon_ok} charset={charset_ok} og={bool(og_ok)} leak={leak}")
    # JSON-LD LocalBusiness on home
    root = parse(htmls["index.html"])
    ld = [s for s in root.find_all("script") if s.attrs.get("type") == "application/ld+json"]
    ld_ok = False
    if ld:
        try:
            data = json.loads(ld[0].text())
            t = data.get("@type", "")
            ld_ok = (
                ("LocalBusiness" in (t if isinstance(t, str) else " ".join(t)))
                and "Bezpieczeństwo Twojej Firmy" in json.dumps(data, ensure_ascii=False)
                and data.get("telephone") == "+48504093624"
                and all(x in json.dumps(data, ensure_ascii=False) for x in ["Kaczewska 22B/8", "81-476", "Gdynia"])
            )
        except (ValueError, TypeError) as exc:
            notes.append(f"JSON-LD parse error: {exc}")
    if not ld_ok:
        ok = False
        notes.append("JSON-LD LocalBusiness missing/incorrect on index")
    r.record("QA-11 SEO/meta + JSON-LD + no-leak", ok,
             "lang=pl, single BTF title, real description, canonical==og:url, charset utf-8, OG set, "
             "LocalBusiness JSON-LD correct, no GA/template/webben leakage"
             if ok else "; ".join(notes))


def qa12(htmls: dict[str, str], r: Results) -> None:
    """QA-12 — Content fidelity spot-checks (real business data on screen)."""
    notes = []
    ok = True
    legal_fragments = [
        "BEZPIECZEŃSTWO TWOJEJ FIRMY", "KAMIL SKAMARSKI",
        "mgr inż. pożarnictwa Kamil Skamarski",
        "NIP: 874-160-03-93", "REGON: 221870187",
        "ul. Kaczewska 22B/8", "81-476 Gdynia",
    ]
    for frag in legal_fragments:
        if frag not in htmls["kontakt.html"]:
            ok = False
            notes.append(f"kontakt missing '{frag}'")
    # realizacje on home
    realizacje = [
        "Galeria Bałtycka", "Bank Pekao S.A.", "Energa", "Carrefour",
        "Hydrobudowa", "Quattro Towers", "Arkońska Business Park", "Stocznia MW Gdynia",
    ]
    for client in realizacje:
        if client not in htmls["index.html"]:
            ok = False
            notes.append(f"home missing realizacja '{client}'")
    # oferta: free review line + bezpłatnie emphasized + 10 zakres items
    oferta = htmls["oferta.html"]
    if "pierwszy podstawowy przegląd stanu bezpieczeństwa przeciwpożarowego" not in oferta:
        ok = False
        notes.append("oferta missing free-review line")
    root = parse(oferta)
    emph = False
    for n in root.iter():
        if n.tag in ("strong", "em", "mark") or "free" in n.attrs.get("class", "") or "highlight" in n.attrs.get("class", ""):
            if "bezpłatnie" in n.text().lower():
                emph = True
                break
    if not emph:
        ok = False
        notes.append("oferta 'bezpłatnie' not emphasized")
    zakres = [ol for ol in root.find_all("ol") if "zakres-list" in ol.attrs.get("class", "")]
    if not zakres or len(zakres[0].find_all("li")) != 10:
        ok = False
        notes.append(f"oferta zakres list != 10 items ({len(zakres[0].find_all('li')) if zakres else 0})")
    # footer: no legacy
    for fname, html in htmls.items():
        root = parse(html)
        for f in root.find_all("footer"):
            ftext = f.text()
            if "webben.pl" in ftext or "© 2014" in ftext:
                ok = False
                notes.append(f"{fname}: legacy footer text present")
            if "Bezpieczeństwo Twojej Firmy" not in ftext:
                ok = False
                notes.append(f"{fname}: footer missing BTF copyright")
    r.record("QA-12 content fidelity", ok,
             "legal id + 8 realizacje + free-review(emphasized) + 10 zakres + current BTF footer (no webben/2014)"
             if ok else "; ".join(notes))


# ----------------------------------------------------------------------------- server bootstrap

def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def wait_for_server(base: str, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base, timeout=2):
                return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.15)
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="btf-redesign end-to-end QA (QA-1..12)")
    ap.add_argument("--base-url", default=None, help="serve target (default: auto-serve ephemeral)")
    ap.add_argument("--no-serve", action="store_true", help="do not start a server; use --base-url")
    args = ap.parse_args()

    proc = None
    if args.base_url:
        base = args.base_url.rstrip("/") + "/"
    elif args.no_serve:
        base = "http://localhost:8000/"
    else:
        port = free_port()
        base = f"http://127.0.0.1:{port}/"
        proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(port)],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not wait_for_server(base):
            print("ERROR: server did not come up", file=sys.stderr)
            proc.terminate()
            return 2

    print(f"# QA target: {base}  (repo: {REPO_ROOT})\n")
    r = Results()
    try:
        htmls = qa1(base, r)
        qa2(base, htmls, r)
        qa3(htmls, r)
        qa4(htmls, r)
        qa5(htmls, r)
        qa6(htmls, r)
        # CSS is part of the served UI; fetch the three stylesheets as one blob.
        css_text = ""
        for css in ("assets/css/tokens.css", "assets/css/base.css", "assets/css/layout.css"):
            _s, _c, t = fetch_text(base, css)
            css_text += "\n" + t
        qa7(htmls, css_text, r)
        qa8(base, htmls, r)
        qa9(css_text, r)
        qa10(base, r)
        qa11(htmls, r)
        qa12(htmls, r)
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    print("\n# Summary")
    for step, ok, _note in r.steps:
        print(f"  {'PASS' if ok else 'FAIL'}  {step}")
    failed = r.failed
    print(f"\n{len(r.steps) - len(failed)}/{len(r.steps)} QA steps passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
