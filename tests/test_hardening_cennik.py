"""Hardening — Cennik integrity (adversarial, position- and identity-anchored).

These tests are deliberately stricter than the slice-5 acceptance tests. The
slice-5 tests key rows into a dict by name, which would survive several
content-corrupting mutations:

  * a DROPPED row that leaves the count short but is masked by parametrization,
  * a DUPLICATED row (two identical names collapse to one dict key),
  * two rows sharing a name (the original prices.py bug where the 16h training
    duplicated the 8h training name — the dict would silently overwrite),
  * a swapped Lp. ordering that scrambles the visible sequence.

Here we pin the FULL ordered (Lp., name [, amount], price) sequence of each
table, assert Lp. runs 1..N with no gaps/dupes, assert names are unique, and
assert the data-corrected training row 7 specifically.
"""
import pytest

# Reuse the canonical expected data from the slice-5 acceptance test so the two
# stay in lockstep; the hardening adds ORDER + UNIQUENESS + IDENTITY assertions.
from test_slice5_cennik import HARDWARES, MISC, TRAININGS, table_by_id, tbody_rows, row_cells


@pytest.fixture
def cennik(docs):
    return docs["cennik.html"]


# --- helpers ----------------------------------------------------------------
def lp_sequence(table):
    """The first cell of every body row, as the printed Lp. number."""
    return [row_cells(tr)[0] for tr in tbody_rows(table)]


def names(table):
    return [row_cells(tr)[1] for tr in tbody_rows(table)]


# --- Lp. numbering is a contiguous 1..N with no gaps or duplicates ----------
@pytest.mark.parametrize(
    "block_id,count",
    [("cennik-sprzet", 23), ("cennik-uslugi", 11), ("cennik-szkolenia", 7)],
)
def test_lp_numbers_are_contiguous_1_to_n(cennik, block_id, count):
    table = table_by_id(cennik, block_id)
    assert table is not None, f"{block_id} table missing"
    lps = lp_sequence(table)
    assert lps == [str(i) for i in range(1, count + 1)], (
        f"{block_id}: Lp. column must read 1..{count} in order, got {lps}"
    )


# --- no name appears twice in any table (catches a DUPLICATED row) ----------
@pytest.mark.parametrize("block_id", ["cennik-sprzet", "cennik-uslugi", "cennik-szkolenia"])
def test_row_names_are_unique(cennik, block_id):
    table = table_by_id(cennik, block_id)
    ns = names(table)
    dupes = {n for n in ns if ns.count(n) > 1}
    assert not dupes, f"{block_id}: duplicate row name(s) {dupes}"


# --- equipment: the full ordered name list is exactly the expected list ------
def test_equipment_full_ordered_names(cennik):
    table = table_by_id(cennik, "cennik-sprzet")
    assert names(table) == HARDWARES, (
        "sprzęt gaśniczy names must match the verbatim list in exact order"
    )


# --- usługi: the full ordered (name, price) sequence is pinned --------------
def test_services_full_ordered_name_price(cennik):
    table = table_by_id(cennik, "cennik-uslugi")
    rows = [(row_cells(tr)[1], row_cells(tr)[2]) for tr in tbody_rows(table)]
    assert rows == MISC, (
        "usługi rows must match the verbatim (name, price) sequence in exact order"
    )


# --- a single swapped price digit must be caught (e.g. 900,00 -> 90,00) ------
def test_services_no_price_digit_dropped(cennik):
    """The most expensive line ('Opracowanie Instrukcji...') must be od 900,00,
    NOT a dropped-digit od 90,00; and the audyt line stays od 800,00."""
    table = table_by_id(cennik, "cennik-uslugi")
    rows = {row_cells(tr)[1]: row_cells(tr)[2] for tr in tbody_rows(table)}
    assert rows["Opracowanie Instrukcji Bezpieczeństwa PPOŻ."] == "od 900,00"
    assert rows["Opracowanie Instrukcji Bezpieczeństwa PPOŻ."] != "od 90,00"
    assert rows["Audyt bezpieczeństwa ppoż."] == "od 800,00"
    # the free review must stay free, never accidentally priced
    assert rows["Przegląd stanu bezp. pożarowego"] == "bezpłatnie"
    # the recurring-fee line keeps its /miesiąc suffix
    assert rows["Stały nadzór nad obiektem"] == "od 200,00/miesiąc"


# --- szkolenia: the full ordered (name, amount, price) sequence is pinned ----
def test_trainings_full_ordered_rows(cennik):
    table = table_by_id(cennik, "cennik-szkolenia")
    rows = [
        (row_cells(tr)[1], row_cells(tr)[2], row_cells(tr)[3])
        for tr in tbody_rows(table)
    ]
    assert rows == TRAININGS, (
        "szkolenia rows must match the verbatim (name, amount, price) sequence "
        "in exact order"
    )


# --- the data-corrected row 7 is asserted directly --------------------------
def test_training_row7_is_kierownicze_16h_190(cennik):
    """Row 7 (the 16h / 190,00 PPOŻ. training) must be the corrected
    '...kierownicze' name, and the old duplicate '...robotnicze' must NOT
    appear on any 16h row."""
    table = table_by_id(cennik, "cennik-szkolenia")
    rows = [
        (row_cells(tr)[1], row_cells(tr)[2], row_cells(tr)[3])
        for tr in tbody_rows(table)
    ]
    name7, amount7, price7 = rows[6]  # 0-indexed row 7
    assert name7 == "Szkolenie BHP z elementami PPOŻ. okresowe stanowiska kierownicze"
    assert amount7 == "16h"
    assert price7 == "190,00"

    # No 16h training is labelled "...robotnicze" (would be the reverted bug).
    by_amount_16h = [(n, a, p) for (n, a, p) in rows if a == "16h"]
    assert all("robotnicze" not in n for (n, a, p) in by_amount_16h), (
        "no 16h training row may be named '...robotnicze' (old duplicate bug)"
    )
    # Exactly two 16h rows (standard kierownicze 140,00 + PPOŻ. kierownicze 190,00).
    assert len(by_amount_16h) == 2, "exactly two trainings run 16h"
    # Both 16h rows are 'kierownicze'.
    assert all("kierownicze" in n for (n, a, p) in by_amount_16h)


# --- the PPOŻ. 8h/16h prices must not be swapped (150,00 vs 190,00) ----------
def test_training_ppoz_prices_not_swapped(cennik):
    table = table_by_id(cennik, "cennik-szkolenia")
    by_name = {}
    for tr in tbody_rows(table):
        c = row_cells(tr)
        by_name[c[1]] = (c[2], c[3])
    assert by_name["Szkolenie BHP z elementami PPOŻ. okresowe stanowiska robotnicze"] == ("8h", "150,00")
    assert by_name["Szkolenie BHP z elementami PPOŻ. okresowe stanowiska kierownicze"] == ("16h", "190,00")


# --- the netto/brutto footnotes are attached to the RIGHT tables ------------
def test_footnotes_attached_to_correct_tables(cennik):
    """A mutation that swaps the netto/brutto footnotes between tables (e.g.
    putting 'brutto' under sprzęt) would corrupt tax semantics silently."""
    sprzet = table_by_id(cennik, "cennik-sprzet")
    uslugi = table_by_id(cennik, "cennik-uslugi")
    szkolenia = table_by_id(cennik, "cennik-szkolenia")

    def foot_text(table):
        tfoot = table.find("tfoot")
        return tfoot.text if tfoot else ""

    assert "cenami netto" in foot_text(sprzet), "sprzęt footnote must say netto"
    assert "brutto" not in foot_text(sprzet)
    assert "cenami netto" in foot_text(uslugi), "usługi footnote must say netto"
    assert "brutto" not in foot_text(uslugi)
    assert "cenami brutto" in foot_text(szkolenia), "szkolenia footnote must say brutto"
    assert "co najmniej 3 osób" in foot_text(szkolenia)
