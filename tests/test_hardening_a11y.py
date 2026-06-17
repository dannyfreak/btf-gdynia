"""Hardening — accessibility boundaries (adversarial).

  * every <img> declares a non-empty alt (decorative SVGs use aria-hidden,
    not <img>, so all <img> here are content),
  * heading order skips no level on any page (h1 -> h3 with no h2 is a defect),
  * exactly one <h1> per page,
  * the hamburger keeps aria-expanded='false' initially and aria-controls
    matching the nav id.
"""
import pytest
from conftest import PAGES

ALL = PAGES + ["404.html"]


def doc_for(page, docs):
    import conftest
    return docs[page] if page in docs else conftest.parse(page)


# --- every content <img> has a non-empty alt --------------------------------
@pytest.mark.parametrize("page", ALL)
def test_every_img_has_nonempty_alt(page, docs):
    doc = doc_for(page, docs)
    for img in doc.find_all("img"):
        alt = img.attrs.get("alt")
        assert alt is not None, f"{page}: <img src={img.attrs.get('src')}> missing alt"
        assert alt.strip() != "", (
            f"{page}: <img src={img.attrs.get('src')}> has empty alt"
        )


# --- exactly one h1 per page ------------------------------------------------
@pytest.mark.parametrize("page", ALL)
def test_exactly_one_h1(page, docs):
    doc = doc_for(page, docs)
    h1s = doc.find_all("h1")
    assert len(h1s) == 1, f"{page}: expected exactly one <h1>, found {len(h1s)}"


# --- heading order never skips a level (document order) ---------------------
@pytest.mark.parametrize("page", ALL)
def test_heading_order_has_no_skipped_level(page, docs):
    doc = doc_for(page, docs)
    levels = [
        int(n.tag[1])
        for n in doc.root.walk()
        if n.tag in ("h1", "h2", "h3", "h4", "h5", "h6")
    ]
    assert levels, f"{page}: page has no headings"
    assert levels[0] == 1, f"{page}: first heading must be <h1>, got h{levels[0]}"
    prev = levels[0]
    for lvl in levels[1:]:
        # Going deeper may only increase by ONE level at a time; going shallower
        # (back up the tree) may jump any amount.
        if lvl > prev:
            assert lvl == prev + 1, (
                f"{page}: heading order skips a level (h{prev} -> h{lvl}); "
                f"sequence={levels}"
            )
        prev = lvl


# --- hamburger toggle a11y wiring -------------------------------------------
@pytest.mark.parametrize("page", ALL)
def test_hamburger_aria_wiring(page, docs):
    doc = doc_for(page, docs)
    header = doc.find("header")
    nav = header.find("nav")
    nav_id = nav.attrs.get("id")
    assert nav_id, f"{page}: nav must declare an id"
    toggles = [b for b in header.find_all("button") if b.attrs.get("aria-controls")]
    assert toggles, f"{page}: header must contain a toggle button with aria-controls"
    btn = toggles[0]
    assert btn.attrs.get("aria-controls") == nav_id, (
        f"{page}: toggle aria-controls ('{btn.attrs.get('aria-controls')}') must "
        f"match nav id ('{nav_id}')"
    )
    assert btn.attrs.get("aria-expanded") == "false", (
        f"{page}: toggle must start with aria-expanded='false', got "
        f"'{btn.attrs.get('aria-expanded')}'"
    )
    # the button must carry an accessible name (aria-label) since its content
    # is an aria-hidden SVG with no text.
    assert btn.attrs.get("aria-label", "").strip() or btn.text.strip(), (
        f"{page}: toggle button must have an accessible name"
    )


# --- skip-link points at the main landmark ----------------------------------
@pytest.mark.parametrize("page", ALL)
def test_skip_link_targets_main(page, docs):
    doc = doc_for(page, docs)
    skips = [a for a in doc.find_all("a") if a.has_class("skip-link")]
    assert skips, f"{page}: missing skip-link"
    href = skips[0].attrs.get("href", "")
    assert href.startswith("#"), f"{page}: skip-link must be an in-page anchor, got {href}"
    target_id = href[1:]
    ids = {n.attrs.get("id") for n in doc.root.walk()}
    assert target_id in ids, f"{page}: skip-link target #{target_id} has no matching element"
