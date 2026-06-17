"""Slice 1 — Site shell: header + footer, consistent across all five pages."""
import pytest
from conftest import PAGES, resolves_to, strip_fragment


def header_of(doc):
    return doc.find("header")


def footer_of(doc):
    return doc.find("footer")


def nav_of(doc):
    hdr = header_of(doc)
    return hdr.find("nav") if hdr else None


# Slice1-1 -------------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_page_has_header_chrome(docs, page):
    doc = docs[page]
    hdr = header_of(doc)
    assert hdr is not None, f"{page}: missing <header>"
    nav = hdr.find("nav")
    assert nav is not None, f"{page}: header missing <nav>"
    assert nav.attrs.get("aria-label") or nav.attrs.get("aria-labelledby"), (
        f"{page}: nav must have an accessible name"
    )
    assert "bezpieczeństwo twojej firmy" in hdr.text.lower(), (
        f"{page}: header must show the BTF brand text"
    )


# Slice1-2 -------------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_nav_links_to_all_five_pages_relative(docs, page):
    nav = nav_of(docs[page])
    hrefs = [a.attrs.get("href", "") for a in nav.find_all("a")]
    for target in PAGES:
        assert any(resolves_to(h, target) for h in hrefs), (
            f"{page}: nav missing relative link to {target} (hrefs={hrefs})"
        )
    for h in hrefs:
        base = strip_fragment(h)
        assert not base.startswith(("http://", "https://", "/")), (
            f"{page}: nav href must be relative, got {h}"
        )


# Slice1-3 -------------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_active_nav_marks_current_page(docs, page):
    nav = nav_of(docs[page])
    current = []
    for a in nav.find_all("a"):
        is_current = a.attrs.get("aria-current") == "page" or a.has_class(
            "is-current", "active", "current"
        )
        if is_current:
            current.append(a)
    assert len(current) == 1, f"{page}: exactly one nav link must be current"
    assert resolves_to(current[0].attrs.get("href", ""), page), (
        f"{page}: the current nav link must point to {page}"
    )


# Slice1-4 -------------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_header_phone_cta(docs, page):
    hdr = header_of(docs[page])
    tel_links = [a for a in hdr.find_all("a") if a.attrs.get("href") == "tel:+48504093624"]
    assert tel_links, f"{page}: header must contain a tel:+48504093624 link"
    assert any("504-093-624" in a.text for a in tel_links), (
        f"{page}: header phone link must show 504-093-624"
    )


# Slice1-5 -------------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_bezplatny_przeglad_cta_links_to_offer(docs, page):
    doc = docs[page]
    ctas = [a for a in doc.find_all("a") if "bezpłatny przegląd" in a.text.lower()]
    assert ctas, f"{page}: missing 'Bezpłatny przegląd' CTA"
    assert any(resolves_to(a.attrs.get("href", ""), "oferta.html") for a in ctas), (
        f"{page}: 'Bezpłatny przegląd' CTA must link to oferta.html"
    )


# Slice1-6 -------------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_mobile_menu_toggle_accessible(docs, page):
    hdr = header_of(docs[page])
    nav = hdr.find("nav")
    nav_id = nav.attrs.get("id")
    assert nav_id, f"{page}: nav must have an id for aria-controls"
    buttons = hdr.find_all("button")
    toggles = [b for b in buttons if b.attrs.get("aria-controls") == nav_id]
    assert toggles, f"{page}: header must contain a <button> controlling the nav"
    btn = toggles[0]
    assert btn.attrs.get("aria-label") or btn.text.strip(), (
        f"{page}: toggle button must have an accessible name"
    )
    assert btn.attrs.get("aria-expanded") == "false", (
        f"{page}: toggle must declare aria-expanded='false' initially"
    )


# Slice1-7 -------------------------------------------------------------------
@pytest.mark.parametrize(
    "page,fragment",
    [
        ("index.html", "ul. Kaczewska 22B/8"),
        ("index.html", "81-476 Gdynia"),
        ("index.html", "NIP: 874-160-03-93"),
        ("index.html", "REGON: 221870187"),
        ("index.html", "BEZPIECZEŃSTWO TWOJEJ FIRMY"),
        ("kontakt.html", "ul. Kaczewska 22B/8"),
        ("kontakt.html", "NIP: 874-160-03-93"),
        ("cennik.html", "REGON: 221870187"),
    ],
)
def test_footer_contains_company_data(docs, page, fragment):
    footer = footer_of(docs[page])
    assert footer is not None, f"{page}: missing <footer>"
    assert fragment in footer.text, f"{page}: footer missing '{fragment}'"


# Slice1-8 -------------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_footer_contact_links(docs, page):
    footer = footer_of(docs[page])
    hrefs = [a.attrs.get("href") for a in footer.find_all("a")]
    assert "tel:+48504093624" in hrefs, f"{page}: footer missing tel link"
    assert "mailto:kamilskamarski@gmail.com" in hrefs, f"{page}: footer missing gmail"
    assert "mailto:btf.kontakt@wp.pl" in hrefs, f"{page}: footer missing wp email"


# Slice1-9 -------------------------------------------------------------------
def test_footer_copyright_is_current_not_legacy(docs):
    for page in PAGES:
        footer = footer_of(docs[page])
        text = footer.text
        assert "Bezpieczeństwo Twojej Firmy" in text, f"{page}: footer must name BTF"
        assert "webben.pl" not in text, f"{page}: footer must not contain webben.pl"
        assert "© 2014" not in text, f"{page}: footer must not contain © 2014"


# Slice1-10 ------------------------------------------------------------------
def test_shell_markup_consistent_across_pages(docs):
    # Same five nav targets everywhere.
    def nav_targets(doc):
        hrefs = [strip_fragment(a.attrs.get("href", "")) for a in nav_of(doc).find_all("a")]
        return {h for h in hrefs if h in PAGES}

    target_sets = {p: nav_targets(docs[p]) for p in PAGES}
    for p in PAGES:
        assert target_sets[p] == set(PAGES), f"{p}: nav targets differ {target_sets[p]}"

    # Same footer contact links everywhere.
    def footer_contacts(doc):
        return {
            a.attrs.get("href")
            for a in footer_of(doc).find_all("a")
            if a.attrs.get("href", "").startswith(("tel:", "mailto:"))
        }

    expected = {"tel:+48504093624", "mailto:kamilskamarski@gmail.com", "mailto:btf.kontakt@wp.pl"}
    for p in PAGES:
        assert expected <= footer_contacts(docs[p]), f"{p}: footer contacts differ"
