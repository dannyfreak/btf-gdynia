"""Slice 7 — Deploy + SEO."""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from conftest import DOMAIN, PAGES, REPO_ROOT, is_relative, parse, read_text, strip_fragment

CANONICAL = {
    "index.html": "https://btf-gdynia.pl/",
    "uslugi.html": "https://btf-gdynia.pl/uslugi.html",
    "oferta.html": "https://btf-gdynia.pl/oferta.html",
    "cennik.html": "https://btf-gdynia.pl/cennik.html",
    "kontakt.html": "https://btf-gdynia.pl/kontakt.html",
}


def meta_named(doc, name):
    return [m for m in doc.find_all("meta") if m.attrs.get("name") == name]


def meta_prop(doc, prop):
    return [m for m in doc.find_all("meta") if m.attrs.get("property") == prop]


# Slice7-1 -------------------------------------------------------------------
def test_cname_single_line():
    # Preview phase: served on github.io (no custom domain), so CNAME is
    # intentionally absent. At go-live it must be exactly the domain.
    if not (REPO_ROOT / "CNAME").exists():
        pytest.skip("CNAME not set yet (preview on github.io; bound at go-live)")
    cname = read_text("CNAME")
    assert [l for l in cname.splitlines() if l.strip()] == ["btf-gdynia.pl"], (
        "CNAME must contain exactly the single line 'btf-gdynia.pl'"
    )


def test_nojekyll_exists():
    assert (REPO_ROOT / ".nojekyll").exists(), ".nojekyll must exist"


def test_robots_references_sitemap():
    robots = read_text("robots.txt")
    assert "Sitemap:" in robots and "sitemap.xml" in robots, (
        "robots.txt must contain a Sitemap: line referencing sitemap.xml"
    )


def test_sitemap_well_formed_xml():
    tree = ET.parse(REPO_ROOT / "sitemap.xml")  # raises on malformed XML
    assert tree.getroot() is not None


def test_404_has_chrome():
    doc = parse("404.html")
    assert doc.source.lstrip().lower().startswith("<!doctype html>")
    assert doc.find("header") is not None, "404.html must include the header chrome"
    assert doc.find("footer") is not None, "404.html must include the footer chrome"


# Slice7-2 -------------------------------------------------------------------
@pytest.mark.parametrize("url", list(CANONICAL.values()))
def test_sitemap_lists_each_canonical_url(url):
    tree = ET.parse(REPO_ROOT / "sitemap.xml")
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [el.text.strip() for el in tree.getroot().iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    if not locs:  # fall back without namespace
        locs = [el.text.strip() for el in tree.getroot().iter("loc")]
    assert url in locs, f"sitemap.xml must list {url}"


# Slice7-3 -------------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_head_seo_metadata(docs, page):
    doc = docs[page]
    html = doc.find("html")
    assert html.attrs.get("lang") == "pl", f"{page}: <html> must be lang='pl'"

    titles = doc.find_all("title")
    assert len(titles) == 1 and titles[0].text.strip(), f"{page}: exactly one non-empty <title>"
    assert "BTF" in titles[0].text or "Bezpieczeństwo Twojej Firmy" in titles[0].text

    descs = meta_named(doc, "description")
    assert len(descs) == 1, f"{page}: exactly one meta description"
    content = descs[0].attrs.get("content", "")
    assert content.strip() and "add description" not in content.lower() and "lorem" not in content.lower()

    canon = [l for l in doc.find_all("link") if l.attrs.get("rel") == "canonical"]
    assert len(canon) == 1, f"{page}: exactly one canonical link"
    assert canon[0].attrs.get("href") == CANONICAL[page], f"{page}: wrong canonical"

    charsets = [m for m in doc.find_all("meta") if m.attrs.get("charset")]
    assert len(charsets) == 1 and charsets[0].attrs["charset"].lower() == "utf-8"

    viewport = meta_named(doc, "viewport")
    assert viewport and "width=device-width" in viewport[0].attrs.get("content", "")


# Slice7-4 -------------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_open_graph_metadata(docs, page):
    doc = docs[page]
    for prop in ("og:title", "og:description", "og:image"):
        tags = meta_prop(doc, prop)
        assert tags and tags[0].attrs.get("content", "").strip(), f"{page}: missing {prop}"
    og_type = meta_prop(doc, "og:type")
    assert og_type and og_type[0].attrs.get("content") == "website", f"{page}: og:type must be website"
    og_url = meta_prop(doc, "og:url")
    assert og_url and og_url[0].attrs.get("content") == CANONICAL[page], f"{page}: og:url must be canonical"


# Slice7-5 -------------------------------------------------------------------
def test_jsonld_localbusiness(docs):
    doc = docs["index.html"]
    blocks = [
        s for s in doc.find_all("script")
        if s.attrs.get("type") == "application/ld+json"
    ]
    assert blocks, "index.html must contain an ld+json block"
    # Extract raw JSON text from source (script content is skipped in DOM text).
    raw = re.search(
        r'<script type="application/ld\+json">(.*?)</script>',
        doc.source, re.DOTALL,
    )
    assert raw, "could not locate ld+json content"
    data = json.loads(raw.group(1))
    assert "LocalBusiness" in data.get("@type", ""), "JSON @type must be LocalBusiness"
    assert "Bezpieczeństwo Twojej Firmy" in data.get("name", "")
    assert data.get("telephone") == "+48504093624"
    addr = json.dumps(data.get("address", {}), ensure_ascii=False)
    assert "Kaczewska 22B/8" in addr and "81-476" in addr and "Gdynia" in addr


# Slice7-6 -------------------------------------------------------------------
@pytest.mark.parametrize("page", ["index.html", "kontakt.html"])
def test_favicon_resolves(docs, page):
    doc = docs[page]
    icons = [l for l in doc.find_all("link") if "icon" in l.attrs.get("rel", "")]
    assert icons, f"{page}: missing <link rel='icon'>"
    href = icons[0].attrs.get("href", "")
    assert (REPO_ROOT / href).exists(), f"{page}: favicon {href} must exist"


# Slice7-7 -------------------------------------------------------------------
def test_no_legacy_leakage(docs):
    for page in PAGES:
        src = docs[page].source
        assert "google-analytics.com" not in src, f"{page}: GA leak"
        assert "{{" not in src and "{%" not in src, f"{page}: Tornado template token leak"
        assert "static_url(" not in src, f"{page}: static_url leak"


# Slice7-8 -------------------------------------------------------------------
def test_no_broken_internal_links_or_assets():
    pages = PAGES + ["404.html"]
    for page in pages:
        doc = parse(page)
        refs = []
        for n in doc.root.walk():
            for attr in ("href", "src"):
                val = n.attrs.get(attr)
                if val and is_relative(val):
                    refs.append(strip_fragment(val))
        for ref in refs:
            if not ref:
                continue
            target = (REPO_ROOT / ref).resolve()
            assert target.exists(), f"{page}: broken reference '{ref}'"
