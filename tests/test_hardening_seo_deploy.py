"""Hardening — SEO / deploy integrity (adversarial).

Catches the silent corruptions that break indexing or social cards:
  * a canonical / og:url that does not match the page (or each other),
  * a sitemap <loc> typo or a loc whose domain drifts from the CNAME,
  * CNAME drift from 'btf-gdynia.pl',
  * a per-page <title> regressing to the legacy 'add description' placeholder
    or all pages sharing one title.
"""
import re
import xml.etree.ElementTree as ET

import pytest
from conftest import DOMAIN, PAGES, REPO_ROOT, read_text

CANONICAL = {
    "index.html": "https://btf-gdynia.pl/",
    "uslugi.html": "https://btf-gdynia.pl/uslugi.html",
    "oferta.html": "https://btf-gdynia.pl/oferta.html",
    "cennik.html": "https://btf-gdynia.pl/cennik.html",
    "kontakt.html": "https://btf-gdynia.pl/kontakt.html",
}
EXPECTED_DOMAIN = "btf-gdynia.pl"

PLACEHOLDERS = ("add description", "add title", "lorem", "untitled", "document")


def canonical_href(doc):
    links = [l for l in doc.find_all("link") if l.attrs.get("rel") == "canonical"]
    return links[0].attrs.get("href") if links else None


def og_url(doc):
    tags = [m for m in doc.find_all("meta") if m.attrs.get("property") == "og:url"]
    return tags[0].attrs.get("content") if tags else None


# --- canonical and og:url match the page AND each other ---------------------
@pytest.mark.parametrize("page", PAGES)
def test_canonical_matches_page(docs, page):
    assert canonical_href(docs[page]) == CANONICAL[page], (
        f"{page}: canonical must be {CANONICAL[page]}"
    )


@pytest.mark.parametrize("page", PAGES)
def test_og_url_matches_canonical(docs, page):
    can = canonical_href(docs[page])
    ogu = og_url(docs[page])
    assert ogu == can, (
        f"{page}: og:url ({ogu}) must equal canonical ({can})"
    )


@pytest.mark.parametrize("page", PAGES)
def test_canonical_domain_matches_cname(docs, page):
    can = canonical_href(docs[page])
    assert EXPECTED_DOMAIN in can, (
        f"{page}: canonical must live under {EXPECTED_DOMAIN}, got {can}"
    )


# --- per-page title is real and unique --------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_title_not_placeholder(docs, page):
    titles = docs[page].find_all("title")
    assert len(titles) == 1, f"{page}: exactly one <title>"
    t = titles[0].text.strip().lower()
    assert t, f"{page}: <title> must be non-empty"
    for ph in PLACEHOLDERS:
        assert ph not in t, f"{page}: <title> must not be the placeholder '{ph}'"


def test_titles_are_unique_per_page(docs):
    titles = {p: docs[p].find_all("title")[0].text.strip() for p in PAGES}
    assert len(set(titles.values())) == len(PAGES), (
        f"each page must have a distinct <title>; got {titles}"
    )


# --- meta description is real and unique-ish --------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_meta_description_real(docs, page):
    descs = [m for m in docs[page].find_all("meta") if m.attrs.get("name") == "description"]
    assert len(descs) == 1, f"{page}: exactly one meta description"
    content = descs[0].attrs.get("content", "").strip().lower()
    assert content, f"{page}: meta description empty"
    for ph in PLACEHOLDERS:
        assert ph not in content, f"{page}: meta description placeholder '{ph}'"


# --- CNAME exact, single line, no whitespace drift --------------------------
def test_cname_exact_single_line():
    # Preview phase: CNAME intentionally absent (github.io). Enforced at go-live.
    if not (REPO_ROOT / "CNAME").exists():
        pytest.skip("CNAME not set yet (preview phase)")
    raw = read_text("CNAME")
    lines = [l for l in raw.splitlines() if l.strip()]
    assert lines == [EXPECTED_DOMAIN], f"CNAME must be exactly '{EXPECTED_DOMAIN}'"
    # no leading scheme, no trailing slash, no www drift
    only = lines[0]
    assert not only.startswith(("http://", "https://"))
    assert not only.endswith("/")
    assert only == EXPECTED_DOMAIN  # not 'www.btf-gdynia.pl' or a typo


# --- sitemap loc set exactly equals the canonical set -----------------------
def test_sitemap_locs_exactly_match_canonicals():
    tree = ET.parse(REPO_ROOT / "sitemap.xml")
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locs = [el.text.strip() for el in tree.getroot().iter(f"{ns}loc")]
    if not locs:
        locs = [el.text.strip() for el in tree.getroot().iter("loc")]
    assert set(locs) == set(CANONICAL.values()), (
        f"sitemap locs must exactly match the five canonical URLs; got {locs}"
    )
    # no duplicate loc entries (a duplicated <url> block)
    assert len(locs) == len(set(locs)), f"sitemap has duplicate <loc>: {locs}"
    # every loc lives under the right domain (catches a typo'd host)
    for loc in locs:
        assert loc.startswith(f"https://{EXPECTED_DOMAIN}/"), (
            f"sitemap loc domain drift: {loc}"
        )


def test_robots_sitemap_url_domain():
    robots = read_text("robots.txt")
    m = re.search(r"Sitemap:\s*(\S+)", robots)
    assert m, "robots.txt must declare a Sitemap: line"
    url = m.group(1)
    assert url == f"https://{EXPECTED_DOMAIN}/sitemap.xml", (
        f"robots Sitemap URL must point at the canonical domain, got {url}"
    )


# --- JSON-LD identity stays intact ------------------------------------------
def test_jsonld_name_and_type(docs):
    import json
    src = docs["index.html"].source
    raw = re.search(r'<script type="application/ld\+json">(.*?)</script>', src, re.DOTALL)
    assert raw, "JSON-LD block missing"
    data = json.loads(raw.group(1))
    assert "LocalBusiness" in data.get("@type", "")
    assert data.get("name") == "Bezpieczeństwo Twojej Firmy — Kamil Skamarski", (
        "JSON-LD business name drifted"
    )
    assert data.get("url") == CANONICAL["index.html"], "JSON-LD url must be the canonical home URL"
