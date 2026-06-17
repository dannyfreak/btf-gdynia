"""Hardening — navigation & link integrity (adversarial).

The slice-1 tests verify each page is *reachable* from nav and that exactly one
link is marked current. They do NOT verify the visible LABEL→href pairing, so a
mutation that points the "Cennik" label at kontakt.html (while still linking to
cennik.html somewhere) would survive. These tests pin the label→target map, the
header CTA target, and the active-state correctness.
"""
import pytest
from conftest import PAGES, resolves_to, strip_fragment

ALL = PAGES + ["404.html"]

# Visible nav label -> page it must resolve to.
NAV_LABEL_TARGET = {
    "O firmie": "index.html",
    "Usługi": "uslugi.html",
    "Oferta": "oferta.html",
    "Cennik": "cennik.html",
    "Kontakt": "kontakt.html",
}


def header_of(doc):
    return doc.find("header")


def primary_nav(doc):
    hdr = header_of(doc)
    nav = hdr.find("nav") if hdr else None
    return nav


@pytest.mark.parametrize("page", ALL)
def test_nav_label_points_at_correct_page(page, docs, repo_root):
    import conftest
    doc = docs[page] if page in docs else conftest.parse(page)
    nav = primary_nav(doc)
    assert nav is not None, f"{page}: header nav missing"
    label_to_href = {}
    for a in nav.find_all("a"):
        label = a.text.strip()
        if label in NAV_LABEL_TARGET:
            label_to_href[label] = a.attrs.get("href", "")
    # all five labels present
    assert set(label_to_href) == set(NAV_LABEL_TARGET), (
        f"{page}: nav labels {set(label_to_href)} != {set(NAV_LABEL_TARGET)}"
    )
    # each label resolves to its own correct target (not a swapped page)
    for label, target in NAV_LABEL_TARGET.items():
        assert resolves_to(label_to_href[label], target), (
            f"{page}: nav label '{label}' must link to {target}, "
            f"got '{label_to_href[label]}'"
        )


@pytest.mark.parametrize("page", PAGES)
def test_header_cta_resolves_to_oferta(docs, page):
    """The header's 'Bezpłatny przegląd' CTA must resolve to oferta.html on
    every page — a mutation pointing it at cennik/kontakt would silently kill
    the primary conversion path."""
    hdr = header_of(docs[page])
    ctas = [a for a in hdr.find_all("a") if "bezpłatny przegląd" in a.text.lower()]
    assert ctas, f"{page}: header missing 'Bezpłatny przegląd' CTA"
    for a in ctas:
        assert resolves_to(a.attrs.get("href", ""), "oferta.html"), (
            f"{page}: header CTA must resolve to oferta.html, got "
            f"'{a.attrs.get('href')}'"
        )


@pytest.mark.parametrize("page", PAGES)
def test_exactly_one_aria_current_and_it_is_self(docs, page):
    """aria-current='page' appears exactly once site-wide on each page and marks
    the page's OWN nav entry (catches an active-state pointing at a sibling)."""
    doc = docs[page]
    currents = [
        a for a in doc.find_all("a")
        if a.attrs.get("aria-current") == "page"
    ]
    assert len(currents) == 1, (
        f"{page}: expected exactly one aria-current='page', found {len(currents)}"
    )
    assert resolves_to(currents[0].attrs.get("href", ""), page), (
        f"{page}: the current link must point at {page}, got "
        f"'{currents[0].attrs.get('href')}'"
    )


@pytest.mark.parametrize("page", PAGES)
def test_no_nav_link_is_absolute_or_external(docs, page):
    """Nav links must stay relative so the site works under the custom domain
    and any subpath; an absolute '/uslugi.html' or external URL is a regression."""
    nav = primary_nav(docs[page])
    for a in nav.find_all("a"):
        href = strip_fragment(a.attrs.get("href", ""))
        assert not href.startswith(("http://", "https://", "/")), (
            f"{page}: nav href must be relative, got '{href}'"
        )


def test_brand_returns_home_on_every_page(docs):
    """The header brand/logo must link back to index.html everywhere."""
    for page in ALL:
        import conftest
        doc = docs[page] if page in docs else conftest.parse(page)
        hdr = header_of(doc)
        brand = next((a for a in hdr.find_all("a") if a.has_class("brand")), None)
        assert brand is not None, f"{page}: header brand link missing"
        assert resolves_to(brand.attrs.get("href", ""), "index.html"), (
            f"{page}: brand must link home, got '{brand.attrs.get('href')}'"
        )
