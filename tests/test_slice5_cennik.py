"""Slice 5 — Cennik (cennik.html)."""
import re

import pytest
from conftest import read_text


@pytest.fixture
def cennik(docs):
    return docs["cennik.html"]


def table_by_id(cennik, block_id):
    """Return the <table> inside the price-block with the given id."""
    for n in cennik.root.walk():
        if n.tag in ("div", "section") and n.attrs.get("id") == block_id:
            return n.find("table")
    return None


def tbody_rows(table):
    tbody = table.find("tbody")
    return tbody.find_all("tr")


def row_cells(tr):
    return [td.text for td in tr.find_all("td")]


HARDWARES = [
    "Gaśnica proszkowa GP-1x ABC",
    "Gaśnica proszkowa GP-1z BC",
    "Gaśnica proszkowa GP – 2z BC",
    "Gaśnica proszkowa GP – 4x ABC",
    "Gaśnica proszkowa GP – 6x ABC",
    "Gaśnica proszkowa GP – 6x BC",
    "Gaśnica proszkowa GP – 9x ABC",
    "Gaśnica proszkowa GP – 12x ABC",
    "Gaśnica śniegowa GSE – 2x",
    "Gaśnica śniegowa GS – 5x",
    "Gaśnica pianowa GW 6x AB",
    "Urządzenie gaśnicze CUG 1x",
    "Urządzenie gaśnicze CUG 2x",
    "UGS 2x",
    "Spray gaśniczy AFFF",
    "Koc gaśniczy",
    "Przegląd gaśnicy",
    "Konserwacja gaśnicy GP-1 (wymiana proszku)",
    "Konserwacja gaśnicy GP-2 (wymiana proszku)",
    "Konserwacja gaśnicy GP-4 (wymiana proszku)",
    "Legalizacja UDT gaśnicy GP – 6x",
    "Legalizacja UDT gaśnicy GP – 9x",
    "Legalizacja UDT gaśnicy GP – 12x",
]

MISC = [
    ("Opracowanie Instrukcji Bezpieczeństwa PPOŻ.", "od 900,00"),
    ("Aktualizacja Instrukcji Bezpieczeństwa PPOŻ.", "od 500,00"),
    ("Opracowanie dokumentacji dla ubezpieczyciela", "od 700,00"),
    ("Audyt bezpieczeństwa ppoż.", "od 800,00"),
    ("Ćwiczenia ewakuacyjne z symulowanym zadymieniem", "od 1200,00"),
    ("Plany ewakuacyjne w formacie .dwg", "od 200,00"),
    ("Próby wydajności i ciśnienia hydrantów wew. i zew.", "od 300,00"),
    ("Doradztwo i opiniowanie", "od 150,00"),
    ("Stały nadzór nad obiektem", "od 200,00/miesiąc"),
    ("Przegląd stanu bezp. pożarowego", "bezpłatnie"),
    ("Oznakowanie obiektu", "od 300,00"),
]

TRAININGS = [
    ("Szkolenie BHP wstępne", "3h", "40,00"),
    ("Szkolenie BHP okresowe stanowiska robotnicze", "8h", "100,00"),
    ("Szkolenie BHP okresowe stanowiska adm.-biurowe", "8h", "100,00"),
    ("Szkolenie BHP okresowe stanowiska kierownicze", "16h", "140,00"),
    ("Szkolenie BHP z elementami PPOŻ. wstępne", "3h", "60,00"),
    ("Szkolenie BHP z elementami PPOŻ. okresowe stanowiska robotnicze", "8h", "150,00"),
    ("Szkolenie BHP z elementami PPOŻ. okresowe stanowiska kierownicze", "16h", "190,00"),
]


# Slice5-1 -------------------------------------------------------------------
def test_cennik_heading(cennik):
    headings = [
        n.text for n in cennik.root.walk()
        if n.tag in ("h1", "h2", "h3")
    ]
    assert any("cennik" in h.lower() for h in headings), "cennik.html must show a CENNIK heading"


# Slice5-2 -------------------------------------------------------------------
def test_equipment_table_has_23_rows(cennik):
    table = table_by_id(cennik, "cennik-sprzet")
    assert table is not None, "equipment table missing"
    assert len(tbody_rows(table)) == 23, "equipment table must have exactly 23 rows"


@pytest.mark.parametrize("item", HARDWARES)
def test_each_equipment_item_verbatim(cennik, item):
    table = table_by_id(cennik, "cennik-sprzet")
    names = [row_cells(tr)[1] for tr in tbody_rows(table)]
    assert item in names, f"equipment item '{item}' must appear verbatim"


# Slice5-3 -------------------------------------------------------------------
def test_services_table_has_11_rows(cennik):
    table = table_by_id(cennik, "cennik-uslugi")
    assert table is not None, "services price table missing"
    assert len(tbody_rows(table)) == 11, "services table must have exactly 11 rows"


@pytest.mark.parametrize("name,price", MISC)
def test_each_service_price_row(cennik, name, price):
    table = table_by_id(cennik, "cennik-uslugi")
    rows = {row_cells(tr)[1]: row_cells(tr)[2] for tr in tbody_rows(table)}
    assert name in rows, f"services table missing '{name}'"
    assert rows[name] == price, f"'{name}' price must be '{price}', got '{rows[name]}'"


# Slice5-4 -------------------------------------------------------------------
def test_trainings_table_has_7_rows_and_columns(cennik):
    table = table_by_id(cennik, "cennik-szkolenia")
    assert table is not None, "trainings table missing"
    assert len(tbody_rows(table)) == 7, "trainings table must have exactly 7 rows"
    headers = " ".join(th.text for th in table.find("thead").find_all("th"))
    assert "Ilość" in headers, "trainings header must include an 'Ilość' (czas) column"
    assert "Cena" in headers, "trainings header must include a price column"


@pytest.mark.parametrize("name,amount,price", TRAININGS)
def test_each_training_row(cennik, name, amount, price):
    table = table_by_id(cennik, "cennik-szkolenia")
    rows = {}
    for tr in tbody_rows(table):
        cells = row_cells(tr)
        rows[cells[1]] = (cells[2], cells[3])
    assert name in rows, f"trainings table missing '{name}'"
    assert rows[name] == (amount, price), (
        f"'{name}' must be {amount}/{price}, got {rows[name]}"
    )


# Slice5-5 -------------------------------------------------------------------
@pytest.mark.parametrize(
    "footnote",
    [
        "Podane ceny są cenami netto.",
        "Podane ceny są cenami brutto i obowiązują przy szkoleniu dla grupy co najmniej 3 osób.",
    ],
)
def test_footnotes_present(cennik, footnote):
    assert footnote in cennik.text, f"cennik.html must contain footnote '{footnote}'"


# Slice5-6 -------------------------------------------------------------------
def test_tables_degrade_to_cards_on_narrow_viewports(cennik):
    css = read_text("assets/css/layout.css")
    # A small-viewport media query that restyles .price-table.
    blocks = re.findall(
        r"@media[^{]*max-width[^{]*\{(.*?)\n\}", css, re.DOTALL
    )
    assert any(".price-table" in b for b in blocks), (
        "a small-viewport media query must restyle .price-table"
    )
    # Semantic table markup remains.
    table = table_by_id(cennik, "cennik-sprzet")
    assert table.find("thead") and table.find("tbody"), (
        "price tables must use semantic <thead>/<tbody>"
    )
