"""Slice 2 — Home / O firmie (index.html)."""
import pytest
from conftest import resolves_to


@pytest.fixture
def home(docs):
    return docs["index.html"]


# Slice2-1 -------------------------------------------------------------------
def test_exactly_one_h1_about_safety(home):
    h1s = home.find_all("h1")
    assert len(h1s) == 1, f"index.html must have exactly one <h1>, found {len(h1s)}"
    text = h1s[0].text.lower()
    assert any(k in text for k in ("bezpieczeństwo", "ppoż", "bhp")), (
        "the <h1> must reference fire-safety / BHP wording"
    )


# Slice2-2 -------------------------------------------------------------------
def test_hero_ctas_present(home):
    offer_ctas = [
        a for a in home.find_all("a")
        if "bezpłatny przegląd" in a.text.lower()
        and resolves_to(a.attrs.get("href", ""), "oferta.html")
    ]
    assert offer_ctas, "hero must have a 'Bezpłatny przegląd' CTA linking to oferta.html"
    tel = [a for a in home.find_all("a") if a.attrs.get("href") == "tel:+48504093624"]
    assert tel, "hero/page must contain a tel:+48504093624 link"


# Slice2-3 -------------------------------------------------------------------
@pytest.mark.parametrize(
    "fragment",
    [
        "wykwalifikowaną kadrą inżynierów",
        "bezpieczeństwem pożarowym",
        "konkurencyjne ceny",
    ],
)
def test_about_narrative_preserved(home, fragment):
    assert fragment in home.text, f"index.html must contain about copy '{fragment}'"


# Slice2-4 -------------------------------------------------------------------
@pytest.mark.parametrize(
    "client",
    [
        "Galeria Bałtycka",
        "Bank Pekao S.A.",
        "Energa",
        "Carrefour",
        "Hydrobudowa",
        "Quattro Towers",
        "Arkońska Business Park",
        "Stocznia MW Gdynia",
    ],
)
def test_realizacje_clients_present(home, client):
    assert client in home.text, f"index.html must list realizacja '{client}'"


# Slice2-5 -------------------------------------------------------------------
def test_services_teaser_links_to_uslugi(home):
    # A teaser section that links onward to the full services page.
    teasers = [
        n for n in home.root.walk()
        if n.tag == "section" and (n.attrs.get("id") == "uslugi-teaser"
                                   or "teaser" in n.attrs.get("id", ""))
    ]
    assert teasers, "index.html must contain a services teaser section"
    teaser = teasers[0]
    links = [a.attrs.get("href", "") for a in teaser.find_all("a")]
    assert any(resolves_to(h, "uslugi.html") for h in links), (
        "services teaser must link to uslugi.html"
    )
