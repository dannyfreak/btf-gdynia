"""Slice 8 — Image prompts (assets/IMAGE-PROMPTS.md) + img hygiene."""
import re
from pathlib import Path

import pytest
from conftest import PAGES, REPO_ROOT, parse

PROMPTS_PATH = "assets/IMAGE-PROMPTS.md"


def read_prompts():
    return (REPO_ROOT / PROMPTS_PATH).read_text(encoding="utf-8")


def image_slots():
    """Distinct image filenames referenced by <img> src and og:image."""
    slots = set()
    for page in PAGES:
        doc = parse(page)
        for img in doc.find_all("img"):
            src = img.attrs.get("src", "")
            if src:
                slots.add(Path(src).name)
        for m in doc.find_all("meta"):
            if m.attrs.get("property") == "og:image":
                content = m.attrs.get("content", "")
                if content:
                    slots.add(Path(content).name)
    return slots


# Background ----------------------------------------------------------------
def test_prompts_file_exists():
    assert (REPO_ROOT / PROMPTS_PATH).exists(), f"{PROMPTS_PATH} must exist"


@pytest.mark.parametrize("page", PAGES)
def test_every_img_has_alt_and_dimensions(page):
    doc = parse(page)
    for img in doc.find_all("img"):
        src = img.attrs.get("src", "")
        assert img.attrs.get("alt") is not None and img.attrs.get("alt").strip() != "" or img.attrs.get("alt") == "", (
            f"{page}: <img {src}> must declare a non-empty alt"
        )
        # alt must be present and non-empty for content images
        assert img.attrs.get("alt", "").strip(), f"{page}: <img {src}> alt must be non-empty"
        assert img.attrs.get("width"), f"{page}: <img {src}> must declare width"
        assert img.attrs.get("height"), f"{page}: <img {src}> must declare height"


# Slice8-1 -------------------------------------------------------------------
def test_every_slot_has_a_prompt_entry():
    text = read_prompts()
    for slot in image_slots():
        assert slot in text, f"IMAGE-PROMPTS.md must mention slot filename '{slot}'"


# Slice8-2 -------------------------------------------------------------------
@pytest.mark.parametrize("slot", ["hero", "og-default"])
def test_prompt_entry_well_formed(slot):
    text = read_prompts()
    # Find the section/entry that names this slot's filename.
    fname_pat = re.compile(rf"{re.escape(slot)}\.(webp|jpg|jpeg|png|svg)", re.IGNORECASE)
    assert fname_pat.search(text), f"entry for '{slot}' must state a real image filename"
    # Pull a window of text around the slot heading to assert the required fields.
    heading = re.search(rf"(^|\n)#{{1,6}}[^\n]*{re.escape(slot)}[^\n]*\n", text, re.IGNORECASE)
    assert heading, f"IMAGE-PROMPTS.md must have a heading for '{slot}'"
    start = heading.end()
    nxt = re.search(r"\n#{1,6} ", text[start:])
    block = text[start:start + (nxt.start() if nxt else len(text))]
    assert re.search(r"\d+\s*[x×]\s*\d+", block), f"'{slot}' entry must state dimensions WxH"
    assert re.search(r"alt", block, re.IGNORECASE), f"'{slot}' entry must state an alt text line"
    body = re.search(r"(prompt|opis)", block, re.IGNORECASE)
    assert body, f"'{slot}' entry must include a generation prompt body"
    low = block.lower()
    assert any(k in low for k in ("ppoż", "ppoz", "fire", "pożar", "bhp", "gaśnic", "industrial", "przemysł")), (
        f"'{slot}' prompt must reference BTF fire-safety / industrial context"
    )


# Slice8-3 -------------------------------------------------------------------
def test_style_guide_section():
    text = read_prompts()
    assert re.search(r"style guide", text, re.IGNORECASE), "must contain a 'Style guide' section"
    assert "#D7261E" in text, "style guide must specify accent #D7261E"
    assert "#1A1D21" in text, "style guide must specify ink #1A1D21"
    low = text.lower()
    assert "documentary" in low or "dokumentaln" in low, "must specify documentary imagery"
    assert "industrial" in low or "przemysł" in low, "must specify industrial direction"
    assert "lighting" in low or "oświetlenie" in low or "composition" in low or "kompozycj" in low, (
        "must specify consistent lighting/composition"
    )


# Slice8-4 -------------------------------------------------------------------
@pytest.mark.parametrize(
    "exclusion",
    [
        "no generic stock / clip-art look",
        "no glassmorphism",
        "no warped text or fake logos",
        "no extra/melted fingers or distorted hands",
        "no oversaturated neon gradients",
    ],
)
def test_negative_guidance_lists_exclusion(exclusion):
    text = read_prompts()
    assert exclusion in text, f"negative-guidance must list '{exclusion}'"


# Slice8-5 -------------------------------------------------------------------
def test_placeholder_assets_present():
    for page in PAGES:
        doc = parse(page)
        for img in doc.find_all("img"):
            src = img.attrs.get("src", "")
            if src and not src.startswith(("http://", "https://", "data:")):
                assert (REPO_ROOT / src).exists(), f"{page}: placeholder for '{src}' missing"
        for m in doc.find_all("meta"):
            if m.attrs.get("property") == "og:image":
                content = m.attrs.get("content", "")
                if content and not content.startswith(("http://", "https://")):
                    assert (REPO_ROOT / content).exists(), f"og:image placeholder '{content}' missing"
