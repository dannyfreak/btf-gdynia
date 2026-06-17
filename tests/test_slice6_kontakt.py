"""Slice 6 — Kontakt (kontakt.html)."""
import pytest


@pytest.fixture
def kontakt(docs):
    return docs["kontakt.html"]


# Slice6-1 -------------------------------------------------------------------
def test_contact_heading(kontakt):
    headings = [n.text for n in kontakt.root.walk() if n.tag in ("h1", "h2", "h3")]
    assert any("kontakt" in h.lower() for h in headings), "kontakt.html must show a Kontakt heading"


# Slice6-2 -------------------------------------------------------------------
@pytest.mark.parametrize(
    "fragment",
    [
        "BEZPIECZEŃSTWO TWOJEJ FIRMY",
        "KAMIL SKAMARSKI",
        "mgr inż. pożarnictwa Kamil Skamarski",
        "ul. Kaczewska 22B/8",
        "81-476 Gdynia",
        "NIP: 874-160-03-93",
        "REGON: 221870187",
    ],
)
def test_legal_identity_present(kontakt, fragment):
    assert fragment in kontakt.text, f"kontakt.html must contain '{fragment}'"


# Slice6-3 -------------------------------------------------------------------
def test_phone_is_tel_link(kontakt):
    tel = [a for a in kontakt.find_all("a") if a.attrs.get("href") == "tel:+48504093624"]
    assert tel, "kontakt.html must contain a tel:+48504093624 link"
    assert any("504-093-624" in a.text for a in tel), "phone link must show 504-093-624"


# Slice6-4 -------------------------------------------------------------------
@pytest.mark.parametrize("email", ["kamilskamarski@gmail.com", "btf.kontakt@wp.pl"])
def test_email_is_mailto_link(kontakt, email):
    links = [a for a in kontakt.find_all("a") if a.attrs.get("href") == f"mailto:{email}"]
    assert links, f"kontakt.html must contain a mailto:{email} link"
    assert any(email in a.text for a in links), f"mailto link must show {email}"


# Slice6-5 -------------------------------------------------------------------
def test_map_embed_present_and_located(kontakt):
    iframes = kontakt.find_all("iframe")
    maps = [
        f for f in iframes
        if "google.com/maps" in f.attrs.get("src", "") and "output=embed" in f.attrs.get("src", "")
    ]
    assert maps, "kontakt.html must contain a keyless Google Maps embed (output=embed, no API key)"
    # the keyless embed must NOT carry an API key
    assert "key=" not in maps[0].attrs.get("src", ""), "map embed must not contain an API key"
    iframe = maps[0]
    assert iframe.attrs.get("title", "").strip(), "map iframe must have a non-empty title"
    assert iframe.attrs.get("loading") == "lazy", "map iframe must set loading='lazy'"
