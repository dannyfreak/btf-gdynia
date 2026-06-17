"""Slice 0 — Foundation: design tokens, reset, motion baseline, harness."""
import re

import pytest
from conftest import PAGES, REPO_ROOT, parse, read_text

TOKENS_CSS = "assets/css/tokens.css"
BASE_CSS = "assets/css/base.css"


def _all_site_css() -> str:
    """Concatenated text of every CSS file the site ships."""
    css_dir = REPO_ROOT / "assets" / "css"
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(css_dir.glob("*.css")))


# Slice0-1 -------------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_each_page_exists_and_has_doctype(page):
    path = REPO_ROOT / page
    assert path.exists(), f"{page} must exist at the repo root"
    text = read_text(page)
    assert text.strip(), f"{page} must be non-empty"
    assert text.lstrip().lower().startswith("<!doctype html>"), (
        f"{page} must start with a <!doctype html> declaration"
    )


def test_tokens_and_base_css_referenced_by_every_page():
    for page in PAGES:
        source = read_text(page)
        assert TOKENS_CSS in source, f"{page} must reference {TOKENS_CSS}"
        assert BASE_CSS in source, f"{page} must reference {BASE_CSS}"


# Slice0-2 -------------------------------------------------------------------
@pytest.mark.parametrize(
    "token,value_fragment",
    [
        ("--color-accent", "#D7261E"),
        ("--color-ink", "#1A1D21"),
        ("--color-surface", "#FFFFFF"),
        ("--color-surface-2", "#F4F5F7"),
    ],
)
def test_design_token_declared_in_root(token, value_fragment):
    css = read_text(TOKENS_CSS)
    root_match = re.search(r":root\s*\{(.*?)\}", css, re.DOTALL)
    assert root_match, "tokens.css must contain a :root rule"
    root_body = root_match.group(1)
    decl = re.search(re.escape(token) + r"\s*:\s*([^;]+);", root_body)
    assert decl, f"{token} must be declared inside :root"
    assert value_fragment in decl.group(1), (
        f"{token} must resolve to a value containing {value_fragment}"
    )


# Slice0-3 -------------------------------------------------------------------
def test_type_scale_is_fluid():
    css = _all_site_css()
    assert "clamp(" in css, "at least one type token/font-size must use clamp()"


# Slice0-4 -------------------------------------------------------------------
def test_reduced_motion_block_neutralizes_motion():
    css = read_text(BASE_CSS)
    match = re.search(
        r"@media\s*\(\s*prefers-reduced-motion:\s*reduce\s*\)\s*\{(.*?)\n\}",
        css,
        re.DOTALL,
    )
    assert match, "base.css must contain a prefers-reduced-motion: reduce block"
    body = match.group(1)
    neutralized = (
        ("animation-duration" in body and "transition-duration" in body
         and ("0.01ms" in body or "0s" in body))
        or "animation: none" in body
        or "transition: none" in body
    )
    assert neutralized, "reduced-motion block must neutralize animation/transition"


# Slice0-5 -------------------------------------------------------------------
def test_view_transitions_are_opt_in_enhancement():
    css = _all_site_css()
    assert "@view-transition" in css, "site CSS must declare @view-transition"
    vt = re.search(r"@view-transition\s*\{(.*?)\}", css, re.DOTALL)
    assert vt, "@view-transition must be a complete at-rule"
    assert re.search(r"navigation\s*:\s*auto", vt.group(1)), (
        "@view-transition must set navigation: auto"
    )
    # Reduced-motion block from Slice0-4 still present.
    assert "prefers-reduced-motion: reduce" in read_text(BASE_CSS)


# Slice0-6 -------------------------------------------------------------------
def test_accent_sourced_from_token_single_source_of_truth():
    css = _all_site_css()
    assert "var(--color-accent)" in css, "accent must be applied via var(--color-accent)"
    # The literal accent hex appears only in the token definition.
    occurrences = re.findall(r"#D7261E", css, re.IGNORECASE)
    assert len(occurrences) == 1, (
        f"#D7261E must appear exactly once (the token def); found {len(occurrences)}"
    )
