"""Slice 4 — Oferta (oferta.html)."""
import pytest
from conftest import resolves_to

EMPHASIS_TAGS = {"strong", "em", "mark", "b"}
EMPHASIS_CLASSES = ("free", "highlight", "emphasis", "underline", "accent")


@pytest.fixture
def oferta(docs):
    return docs["oferta.html"]


ZAKRES_ITEMS = [
    "analiza i kontrola bieżącego stanu ochrony ppoż.",
    "stały nadzór nad obiektami i terenami",
    "doradztwo i opiniowanie projektów budowlanych",
    "opracowywanie i aktualizacja instrukcji bezpieczeństwa pożarowego",
    "wykonywania planów ewakuacyjnych obiektu w formacie .dwg",
    "prowadzenie szkoleń z zakresu ochrony przeciwpożarowej (teoretyczne i praktyczne)",
    "organizowanie i prowadzenie ćwiczeń ewakuacyjnych",
    "wyposażanie obiektów w znaki ewakuacyjne oraz w podręczny sprzęt gaśniczy",
    "przegląd, konserwacja i legalizacja gaśnic oraz innych systemów ppoż.",
    "próby wydajności i ciśnienia hydrantów wewnętrznych i zewnętrznych",
]


# Slice4-1 -------------------------------------------------------------------
def test_free_first_review_highlighted(oferta):
    assert (
        "pierwszy podstawowy przegląd stanu bezpieczeństwa przeciwpożarowego"
        in oferta.text
    ), "oferta.html must contain the free-first-review line"
    emphasized = []
    for n in oferta.root.walk():
        if n.tag in EMPHASIS_TAGS or n.has_class(*EMPHASIS_CLASSES):
            if "bezpłatnie" in n.text.lower():
                emphasized.append(n)
    assert emphasized, "'bezpłatnie' must appear inside an emphasized element"


# Slice4-2 -------------------------------------------------------------------
def test_offer_intro_narrative(oferta):
    assert "ofertę dotyczącą świadczenia usług z zakresu ochrony przeciwpożarowej" in oferta.text
    assert "ocenić kompetencje, jakość oraz profesjonalizm" in oferta.text


# Slice4-3 -------------------------------------------------------------------
def test_zakres_heading_present(oferta):
    headings = [
        n.text for n in oferta.root.walk()
        if n.tag in ("h1", "h2", "h3", "h4", "h5", "h6")
    ]
    assert any("zakres usług" in h.lower() for h in headings), (
        "oferta.html must contain a 'ZAKRES USŁUG' heading"
    )


def _zakres_list(oferta):
    for n in oferta.root.walk():
        if n.tag in ("ol", "ul") and n.has_class("zakres-list"):
            return n
    return None


@pytest.mark.parametrize("item", ZAKRES_ITEMS)
def test_each_zakres_item_present(oferta, item):
    lst = _zakres_list(oferta)
    assert lst is not None, "oferta.html must contain the zakres list"
    texts = [li.text for li in lst.find_all("li")]
    assert item in texts, f"zakres list must contain item '{item}'"


def test_zakres_list_has_exactly_ten_items(oferta):
    lst = _zakres_list(oferta)
    assert lst is not None
    assert len(lst.find_all("li")) == 10, "ZAKRES USŁUG list must have exactly 10 items"


# Slice4-4 -------------------------------------------------------------------
def test_offer_conversion_cta(oferta):
    assert "zachęcamy do kontaktu" in oferta.text
    hrefs = [a.attrs.get("href", "") for a in oferta.find_all("a")]
    assert any(resolves_to(h, "kontakt.html") for h in hrefs), (
        "oferta.html must link to kontakt.html"
    )
    assert "tel:+48504093624" in hrefs, "oferta.html must contain a tel link"
