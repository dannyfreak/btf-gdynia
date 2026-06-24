"""Carbon site — invariants for the dark redesign.

Verifies the public static surface only (parsed with stdlib html.parser via
conftest). Guards: shell/structure, SEO/meta, content fidelity (cennik 23/11/7,
legal data, realizacje, zakres), keyless map, consent/cookies, no secret/legacy
leakage, deploy files, a11y, and internal-link integrity.
"""
import json
import re
import xml.etree.ElementTree as ET

import pytest
from conftest import (
    DOMAIN, PAGES, REPO_ROOT, is_relative, parse, read_text, resolves_to,
    strip_fragment,
)

ALL = PAGES + ["404.html", "polityka-prywatnosci.html"]
CANONICAL = {
    "index.html": "https://btf-gdynia.pl/",
    "uslugi.html": "https://btf-gdynia.pl/uslugi.html",
    "oferta.html": "https://btf-gdynia.pl/oferta.html",
    "cennik.html": "https://btf-gdynia.pl/cennik.html",
    "kontakt.html": "https://btf-gdynia.pl/kontakt.html",
}


# --- Shell / structure ------------------------------------------------------
@pytest.mark.parametrize("page", ALL)
def test_doctype_and_lang(page):
    src = read_text(page)
    assert src.lstrip().lower().startswith("<!doctype html>"), f"{page}: needs doctype"
    doc = parse(page)
    assert doc.find("html").attrs.get("lang") == "pl", f"{page}: <html lang=pl>"


@pytest.mark.parametrize("page", ALL)
def test_one_h1(page):
    assert len(parse(page).find_all("h1")) == 1, f"{page}: exactly one <h1>"


@pytest.mark.parametrize("page", ALL)
def test_header_footer_nav_skiplink(page):
    doc = parse(page)
    header = doc.find("header")
    assert header is not None and header.has_class("site"), f"{page}: header.site"
    nav = header.find("nav")
    assert nav and nav.attrs.get("aria-label"), f"{page}: header nav needs aria-label"
    assert doc.find("footer") is not None, f"{page}: footer"
    skips = [a for a in doc.find_all("a") if a.has_class("skip-link")]
    assert skips and skips[0].attrs.get("href") == "#main", f"{page}: skip-link → #main"
    ids = {n.attrs.get("id") for n in doc.root.walk()}
    assert "main" in ids, f"{page}: #main target exists"


@pytest.mark.parametrize("page", ALL)
def test_assets_referenced(page):
    src = read_text(page)
    for ref in ("assets/css/carbon.css", "assets/js/carbon-nav.js", "assets/js/consent.js"):
        assert ref in src, f"{page}: must reference {ref}"


@pytest.mark.parametrize("page", ALL)
def test_navtoggle_aria(page):
    header = parse(page).find("header")
    btns = [b for b in header.find_all("button") if b.attrs.get("aria-controls")]
    assert btns, f"{page}: header needs a nav toggle button"
    b = btns[0]
    assert b.attrs.get("aria-expanded") == "false", f"{page}: toggle aria-expanded=false"
    nav = header.find("nav")
    # aria-controls points at the mobile menu container
    assert b.attrs.get("aria-controls") == "mnav", f"{page}: toggle controls #mnav"
    assert b.attrs.get("aria-label") or b.text.strip(), f"{page}: toggle accessible name"
    assert nav is not None


@pytest.mark.parametrize("page", PAGES)
def test_nav_links_all_pages(page):
    nav = parse(page).find("header").find("nav")
    hrefs = [a.attrs.get("href", "") for a in nav.find_all("a")]
    for target in PAGES:
        assert any(resolves_to(h, target) for h in hrefs), f"{page}: nav → {target}"
    assert not any(h.startswith(("http://", "https://", "/")) for h in hrefs), (
        f"{page}: nav links must be relative"
    )


@pytest.mark.parametrize("page", PAGES)
def test_active_nav_marks_self(page):
    nav = parse(page).find("header").find("nav")
    current = [a for a in nav.find_all("a") if a.attrs.get("aria-current") == "page"]
    assert len(current) == 1, f"{page}: exactly one aria-current in header nav"
    assert resolves_to(current[0].attrs.get("href", ""), page), f"{page}: current → self"


# --- Phone / email / CTA ----------------------------------------------------
@pytest.mark.parametrize("page", ALL)
def test_phone_and_footer_contacts(page):
    doc = parse(page)
    assert any(a.attrs.get("href") == "tel:+48504093624" for a in doc.find_all("a")), (
        f"{page}: tel:+48504093624 link"
    )
    footer = doc.find("footer")
    fh = [a.attrs.get("href") for a in footer.find_all("a")]
    assert "tel:+48504093624" in fh, f"{page}: footer tel"
    assert "mailto:kamilskamarski@gmail.com" in fh, f"{page}: footer gmail"
    assert "mailto:btf.kontakt@wp.pl" in fh, f"{page}: footer wp email"


@pytest.mark.parametrize("page", ALL)
def test_footer_privacy_and_cookie_settings(page):
    footer = parse(page).find("footer")
    assert any(resolves_to(a.attrs.get("href", ""), "polityka-prywatnosci.html")
               for a in footer.find_all("a")), f"{page}: footer privacy link"
    assert any("data-cookie-settings" in n.attrs for n in footer.find_all("button")), (
        f"{page}: footer 'Ustawienia cookies' button"
    )


@pytest.mark.parametrize("page", ALL)
def test_footer_copyright_current(page):
    ftext = parse(page).find("footer").text
    assert "Bezpieczeństwo Twojej Firmy" in ftext
    assert "webben.pl" not in ftext and "© 2014" not in ftext


# --- SEO / meta -------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_seo_head(page):
    doc = parse(page)
    titles = doc.find_all("title")
    assert len(titles) == 1 and titles[0].text.strip(), f"{page}: one non-empty title"
    t = titles[0].text
    assert "BTF" in t or "Bezpieczeństwo Twojej Firmy" in t, f"{page}: title names brand"
    metas = doc.find_all("meta")
    desc = [m for m in metas if m.attrs.get("name") == "description"]
    assert desc and desc[0].attrs.get("content", "").strip(), f"{page}: meta description"
    assert "add description" not in desc[0].attrs.get("content", "").lower()
    canon = [l for l in doc.find_all("link") if l.attrs.get("rel") == "canonical"]
    assert canon and canon[0].attrs.get("href") == CANONICAL[page], f"{page}: canonical"
    assert any(m.attrs.get("charset", "").lower() == "utf-8" for m in metas), f"{page}: charset"
    assert any(m.attrs.get("name") == "viewport" and "width=device-width" in m.attrs.get("content", "")
               for m in metas), f"{page}: viewport"


@pytest.mark.parametrize("page", PAGES)
def test_open_graph(page):
    metas = parse(page).find_all("meta")
    og = {m.attrs.get("property"): m.attrs.get("content", "") for m in metas if m.attrs.get("property")}
    assert og.get("og:title"), f"{page}: og:title"
    assert og.get("og:description"), f"{page}: og:description"
    assert og.get("og:type") == "website", f"{page}: og:type=website"
    assert og.get("og:url") == CANONICAL[page], f"{page}: og:url == canonical"
    assert og.get("og:image"), f"{page}: og:image"


def test_jsonld_localbusiness():
    doc = parse("index.html")
    blocks = [n for n in doc.find_all("script") if n.attrs.get("type") == "application/ld+json"]
    assert blocks, "index: JSON-LD block"
    # extract raw JSON from source (parser skips script text)
    m = re.search(r'application/ld\+json"\s*>(.*?)</script>', doc.source, re.DOTALL)
    data = json.loads(m.group(1))
    assert "LocalBusiness" in data["@type"]
    assert "Bezpieczeństwo Twojej Firmy" in data["name"]
    assert data["telephone"] == "+48504093624"
    addr = json.dumps(data["address"], ensure_ascii=False)
    assert "Kaczewska 22B/8" in addr and "81-476" in addr and "Gdynia" in addr


# --- Content fidelity -------------------------------------------------------
@pytest.mark.parametrize("frag", [
    "wykwalifikowaną kadrą inżynierów", "bezpieczeństwem pożarowym", "konkurencyjne ceny",
])
def test_index_about(frag):
    assert frag in parse("index.html").text, f"index about: {frag}"


@pytest.mark.parametrize("client", [
    "Galeria Bałtycka", "Bank Pekao S.A.", "Energa", "Carrefour",
    "Hydrobudowa", "Quattro Towers", "Arkońska Business Park", "Stocznia MW Gdynia",
])
def test_index_realizacje(client):
    assert client in parse("index.html").text, f"index realizacja: {client}"


def test_index_services_teaser_links_uslugi():
    doc = parse("index.html")
    assert any(resolves_to(a.attrs.get("href", ""), "uslugi.html") for a in doc.find_all("a"))


@pytest.mark.parametrize("frag", [
    "Uzgadnianie projektów", "Analiza i kontrola", "Prowadzenie szkoleń",
    "Instrukcje bezpieczeństwa", "Znaki ewakuacyjne", "legalizacja gaśnic",
])
def test_uslugi_core_services(frag):
    assert frag in parse("uslugi.html").text, f"uslugi: {frag}"


def test_oferta_bezplatnie_and_zakres():
    doc = parse("oferta.html")
    free = [n for n in doc.find_all("span") if n.has_class("free")]
    assert free and "bezpłatnie" in " ".join(n.text for n in free).lower()
    ol = [n for n in doc.find_all("ol") if n.has_class("zakres")]
    assert ol, "oferta: .zakres list"
    items = ol[0].find_all("li")
    assert len(items) == 10, f"oferta: zakres must have 10 items, got {len(items)}"


def _tables(doc):
    return doc.find_all("table")


def test_cennik_row_counts():
    doc = parse("cennik.html")
    tables = _tables(doc)
    assert len(tables) == 3, f"cennik: 3 tables, got {len(tables)}"
    counts = []
    for t in tables:
        counts.append(len([tr for tr in t.find_all("tr")
                            if any(td.attrs.get("data-label") == "Nazwa" for td in tr.find_all("td"))]))
    assert counts == [23, 11, 7], f"cennik counts {counts} != [23, 11, 7]"


@pytest.mark.parametrize("frag", [
    "Gaśnica proszkowa GP-1x ABC", "Legalizacja UDT gaśnicy GP-12x",
    "od 900,00", "od 200,00 / mies.", "bezpłatnie",
    "Szkolenie BHP z el. PPOŻ. okresowe — kierownicze", "190,00",
    "Podane ceny są cenami netto.",
    "Ceny brutto, obowiązują przy szkoleniu dla grupy co najmniej 3 osób.",
])
def test_cennik_content(frag):
    assert frag in parse("cennik.html").text, f"cennik: {frag}"


@pytest.mark.parametrize("frag", [
    "Bezpieczeństwo Twojej Firmy — Kamil Skamarski", "mgr inż. pożarnictwa Kamil Skamarski",
    "ul. Kaczewska 22B/8", "81-476 Gdynia", "874-160-03-93", "221870187",
])
def test_kontakt_legal(frag):
    assert frag in parse("kontakt.html").text, f"kontakt: {frag}"


# --- Keyless map (no API key) ----------------------------------------------
def test_kontakt_map_keyless():
    doc = parse("kontakt.html")
    iframes = [f for f in doc.find_all("iframe") if "google.com/maps" in f.attrs.get("src", "")]
    assert iframes, "kontakt: google maps iframe"
    src = iframes[0].attrs.get("src", "")
    assert "output=embed" in src, "kontakt: keyless embed (output=embed)"
    assert "key=" not in src and "AIza" not in src, "kontakt: map must carry NO API key"
    assert iframes[0].attrs.get("loading") == "lazy"


# --- No secret / legacy leakage ---------------------------------------------
def _served_texts():
    out = {p: read_text(p) for p in ALL}
    out["carbon.css"] = read_text("assets/css/carbon.css")
    out["carbon-nav.js"] = read_text("assets/js/carbon-nav.js")
    out["consent.js"] = read_text("assets/js/consent.js")
    return out


@pytest.mark.parametrize("needle", [
    "AIza", "1ee325108516", "license_key", "newrelic",
    "google-analytics.com", "{{", "{%", "static_url(",
])
def test_no_leak(needle):
    for name, txt in _served_texts().items():
        assert needle not in txt, f"{name} must not contain '{needle}'"


def test_fonts_gated_not_imported_in_css():
    css = read_text("assets/css/carbon.css")
    assert "fonts.googleapis.com" not in css, "carbon.css must NOT @import fonts (gated by consent)"
    assert "fonts.googleapis.com" in read_text("assets/js/consent.js"), "consent.js injects fonts"


# --- A11y -------------------------------------------------------------------
@pytest.mark.parametrize("page", ALL)
def test_img_alt(page):
    for img in parse(page).find_all("img"):
        assert img.attrs.get("alt", "").strip(), f"{page}: <img {img.attrs.get('src')}> needs alt"


@pytest.mark.parametrize("page", ALL)
def test_heading_order(page):
    levels = [int(n.tag[1]) for n in parse(page).root.walk() if n.tag in ("h1", "h2", "h3", "h4", "h5", "h6")]
    assert levels and levels[0] == 1, f"{page}: first heading must be h1"
    prev = levels[0]
    for lvl in levels[1:]:
        if lvl > prev:
            assert lvl == prev + 1, f"{page}: heading skips a level: {levels}"
        prev = lvl


# --- Deploy files -----------------------------------------------------------
def test_cname():
    lines = [l for l in read_text("CNAME").splitlines() if l.strip()]
    assert lines == ["btf-gdynia.pl"], "CNAME must be exactly btf-gdynia.pl"


def test_nojekyll_exists():
    assert (REPO_ROOT / ".nojekyll").exists()


def test_robots_sitemap():
    r = read_text("robots.txt")
    assert "Sitemap:" in r and "sitemap.xml" in r


def test_sitemap_locs():
    tree = ET.parse(REPO_ROOT / "sitemap.xml")
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locs = {el.text.strip() for el in tree.getroot().iter(f"{ns}loc")}
    assert locs == set(CANONICAL.values()), f"sitemap locs {locs} != canonicals"


def test_404_has_chrome():
    doc = parse("404.html")
    assert doc.find("header") and doc.find("footer"), "404 needs header+footer"


@pytest.mark.parametrize("page", ["index.html", "kontakt.html"])
def test_favicon_resolves(page):
    icons = [l for l in parse(page).find_all("link") if "icon" in l.attrs.get("rel", "")]
    assert icons, f"{page}: favicon link"
    assert (REPO_ROOT / icons[0].attrs.get("href")).exists(), f"{page}: favicon file exists"


# --- Theme toggle (dark / light) --------------------------------------------
@pytest.mark.parametrize("page", ALL)
def test_theme_bootstrap_before_css(page):
    src = read_text(page)
    assert "btf-theme" in src, f"{page}: theme bootstrap script present"
    assert src.index("btf-theme") < src.index("assets/css/carbon.css"), (
        f"{page}: theme bootstrap must run before carbon.css (no FOUC)"
    )
    assert "prefers-color-scheme" in src, (
        f"{page}: bootstrap must follow system theme when no explicit choice"
    )


@pytest.mark.parametrize("page", ALL)
def test_light_is_default(page):
    html = parse(page).find("html")
    assert html.attrs.get("data-theme") == "light", f"{page}: light must be the default theme"


def test_light_theme_and_toggle_defined():
    css = read_text("assets/css/carbon.css")
    assert '[data-theme="light"]' in css, "carbon.css: light theme block"
    assert ".theme-toggle" in css, "carbon.css: theme-toggle styles"
    js = read_text("assets/js/carbon-nav.js")
    assert "theme-toggle" in js and "btf-theme" in js, "carbon-nav.js: injects theme toggle"
    assert "prefers-color-scheme" in js, "carbon-nav.js: follows live system theme changes"


# --- Internal link / asset integrity ----------------------------------------
@pytest.mark.parametrize("page", ALL)
def test_no_broken_internal_links(page):
    doc = parse(page)
    refs = []
    for n in doc.root.walk():
        for attr in ("href", "src"):
            v = n.attrs.get(attr)
            if v and is_relative(v):
                refs.append(strip_fragment(v))
    for ref in refs:
        if not ref:
            continue
        assert (REPO_ROOT / ref).exists(), f"{page}: broken internal ref → {ref}"
