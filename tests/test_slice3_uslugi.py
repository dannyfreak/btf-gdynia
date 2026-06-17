"""Slice 3 — Usługi (uslugi.html)."""
import pytest
from conftest import contains_emoji


@pytest.fixture
def uslugi(docs):
    return docs["uslugi.html"]


def services_grid(uslugi):
    for n in uslugi.root.walk():
        if n.tag in ("div", "section") and n.has_class("bento"):
            return n
    return None


# Slice3-1 -------------------------------------------------------------------
def test_one_h1_about_services(uslugi):
    h1s = uslugi.find_all("h1")
    assert len(h1s) == 1, f"uslugi.html must have exactly one <h1>, found {len(h1s)}"
    assert "usługi" in h1s[0].text.lower(), "the <h1> must contain 'Usługi'"


# Slice3-2 -------------------------------------------------------------------
@pytest.mark.parametrize(
    "fragment",
    [
        "Uzgadnianie projektów budowlanych",
        "Analiza i kontrola bieżącego stanu ochrony ppoż.",
        "Prowadzenie szkoleń",
        "Opracowywanie i aktualizacja instrukcji bezpieczeństwa pożarowego",
        "Wyposażanie obiektów w znaki ewakuacyjne oraz w podręczny sprzęt gaśniczy",
        "Przegląd, konserwacja i legalizacja gaśnic",
    ],
)
def test_core_services_present(uslugi, fragment):
    assert fragment in uslugi.text, f"uslugi.html must list service '{fragment}'"


# Slice3-3 -------------------------------------------------------------------
def test_services_use_inline_svg_not_emoji(uslugi):
    grid = services_grid(uslugi)
    assert grid is not None, "uslugi.html must have a services grid"
    assert grid.find_all("svg"), "services section must contain inline <svg> icons"
    assert not contains_emoji(grid.text), (
        "services section must not use emoji characters as iconography"
    )


# Slice3-4 -------------------------------------------------------------------
def test_services_laid_out_as_grid(uslugi):
    grid = services_grid(uslugi)
    assert grid is not None, "uslugi.html must have a grid/bento container"
    items = [c for c in grid.element_children if c.has_class("card")]
    assert len(items) >= 2, "the grid must hold two or more service items"
