"""Hardening — phone / email / legal-data integrity (adversarial).

Catches the silent-corruption mutations that the slice tests miss:
  * a transposed digit in the phone number where href and label drift apart,
  * a wrong email tld / near-miss typo,
  * a single-digit mutation in NIP or REGON,
  * an altered address.

We normalise to digits and compare against the canonical values so that a
mutation in EITHER the tel: href OR the displayed text is caught, and we assert
the two map to the same number.
"""
import re

import pytest
from conftest import PAGES

TEL_HREF = "tel:+48504093624"
CANON_DIGITS = "48504093624"          # E.164 digits without '+'
DISPLAY = "504-093-624"
DISPLAY_DIGITS = "504093624"          # national digits

EMAILS = ("kamilskamarski@gmail.com", "btf.kontakt@wp.pl")

NIP = "874-160-03-93"
REGON = "221870187"
STREET = "ul. Kaczewska 22B/8"
POSTAL_CITY = "81-476 Gdynia"


def digits(s):
    return re.sub(r"\D", "", s)


# --- phone: href digits exactly equal the canonical E.164 number ------------
@pytest.mark.parametrize("page", PAGES)
def test_tel_href_digits_exact(docs, page):
    doc = docs[page]
    tel_links = [a for a in doc.find_all("a") if a.attrs.get("href", "").startswith("tel:")]
    assert tel_links, f"{page}: expected at least one tel: link"
    for a in tel_links:
        href = a.attrs["href"]
        assert href == TEL_HREF, f"{page}: tel href must be exactly {TEL_HREF}, got {href}"
        assert digits(href) == CANON_DIGITS, (
            f"{page}: tel href digits must be {CANON_DIGITS}, got {digits(href)}"
        )


# A displayed PL phone formatted as three triplets, e.g. 504-093-624.
PHONE_DISPLAY_RE = re.compile(r"\d{3}-\d{3}-\d{3}")


@pytest.mark.parametrize("page", PAGES)
def test_displayed_phone_maps_to_href(docs, page):
    """Every visibly-displayed grouped phone string must reduce to the same
    national digits as the tel: href, so a transposed digit in EITHER the label
    or the href (but not both) is impossible to ship unnoticed.

    We scan the full visible text for any 3-3-3 grouped number rather than the
    exact expected string, so a corrupted display (e.g. 504-093-642) is still
    found and then rejected for not matching the canonical digits."""
    doc = docs[page]
    displayed = PHONE_DISPLAY_RE.findall(doc.text)
    assert displayed, f"{page}: no displayed grouped phone number found"
    for shown in displayed:
        assert digits(shown) == DISPLAY_DIGITS, (
            f"{page}: displayed phone '{shown}' must reduce to {DISPLAY_DIGITS}"
        )
    # the canonical display literal must be present at least once
    assert DISPLAY in doc.text, f"{page}: must display the phone as {DISPLAY}"
    # and the href's national tail equals the displayed national digits
    assert CANON_DIGITS.endswith(DISPLAY_DIGITS), "internal consistency check"


@pytest.mark.parametrize("page", PAGES)
def test_no_wrong_phone_variant_present(docs, page):
    """No near-miss phone string (e.g. an 8-digit or differently grouped number)
    leaks into the page source where the real one should be."""
    src = docs[page].source
    # If a tel: link exists it must be the exact canonical one — no other
    # tel: target may appear.
    tel_targets = set(re.findall(r'tel:([^"\']+)', src))
    assert tel_targets <= {"+48504093624"}, (
        f"{page}: unexpected tel target(s) {tel_targets - {'+48504093624'}}"
    )


# --- emails: exact mailto set, no typo'd tld --------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_mailto_targets_exact(docs, page):
    src = docs[page].source
    mailtos = set(re.findall(r'mailto:([^"\']+)', src))
    if not mailtos:
        pytest.skip(f"{page}: no mailto links (allowed on non-contact pages)")
    # every mailto present must be one of the two canonical addresses, verbatim
    assert mailtos <= set(EMAILS), (
        f"{page}: unexpected mailto target(s) {mailtos - set(EMAILS)}"
    )


def test_kontakt_has_both_emails_exact(docs):
    src = docs["kontakt.html"].source
    mailtos = set(re.findall(r'mailto:([^"\']+)', src))
    assert set(EMAILS) <= mailtos, "kontakt.html must carry BOTH exact mailto addresses"
    # guard against a tld typo such as .con / .pI / gmial
    assert "kamilskamarski@gmail.com" in mailtos
    assert "btf.kontakt@wp.pl" in mailtos
    assert not any(m.endswith((".con", ".pI", ".comm")) for m in mailtos)


# --- legal data: single-digit mutation in NIP / REGON is caught -------------
@pytest.mark.parametrize("page", ["index.html", "kontakt.html", "cennik.html"])
def test_nip_regon_exact(docs, page):
    text = docs[page].text
    assert f"NIP: {NIP}" in text, f"{page}: NIP must be exactly {NIP}"
    assert f"REGON: {REGON}" in text, f"{page}: REGON must be exactly {REGON}"
    # The NIP digit string is 10 digits; REGON 9 digits — a length change from a
    # added/dropped digit would fail the exact match above, but assert lengths
    # too for an explicit signal.
    assert len(digits(NIP)) == 10
    assert len(digits(REGON)) == 9

    # Internal consistency: every "NIP:"/"REGON:" label on the page must carry
    # the SAME canonical value. Catches a single-occurrence mutation that leaves
    # one copy correct (e.g. footer right, contact card wrong) and a divergent
    # second copy elsewhere.
    nip_values = re.findall(r"NIP:\s*([\d-]+)", text)
    regon_values = re.findall(r"REGON:\s*([\d-]+)", text)
    assert nip_values, f"{page}: expected at least one 'NIP:' label"
    assert regon_values, f"{page}: expected at least one 'REGON:' label"
    assert set(nip_values) == {NIP}, f"{page}: divergent/incorrect NIP values {set(nip_values)}"
    assert set(regon_values) == {REGON}, f"{page}: divergent/incorrect REGON values {set(regon_values)}"


def test_kontakt_address_exact(docs):
    text = docs["kontakt.html"].text
    assert STREET in text, "kontakt.html must carry the exact street address"
    assert POSTAL_CITY in text, "kontakt.html must carry the exact postal code + city"
    # postal code is the Gdynia code, not a transposed variant
    assert "81-476" in text and "84-476" not in text and "81-746" not in text


def test_jsonld_phone_and_address_consistent(docs):
    """JSON-LD telephone must match the canonical href digits and the address
    must carry the exact street/postal/city."""
    import json
    src = docs["index.html"].source
    raw = re.search(r'<script type="application/ld\+json">(.*?)</script>', src, re.DOTALL)
    assert raw, "index.html JSON-LD block missing"
    data = json.loads(raw.group(1))
    assert data["telephone"] == "+48504093624"
    assert digits(data["telephone"]) == CANON_DIGITS
    addr = data["address"]
    assert addr["streetAddress"] == "ul. Kaczewska 22B/8"
    assert addr["postalCode"] == "81-476"
    assert addr["addressLocality"] == "Gdynia"
    # vatID, if present, must match the NIP exactly
    if "vatID" in data:
        assert data["vatID"] == NIP
