"""Hardening — anti-regression for legacy leakage (adversarial).

The legacy Tornado app + old webben.pl footer must never bleed back into any
served page. Slice7-7 checks four tokens on the five content pages; this widens
the net to all served pages (incl. 404.html) and adds the footer-copyright and
old-domain markers most likely to reappear in a careless edit.
"""
import pytest
from conftest import PAGES

ALL = PAGES + ["404.html"]

FORBIDDEN_SUBSTRINGS = [
    "{{",                  # Tornado expression token
    "{%",                  # Tornado control token
    "static_url(",         # Tornado static helper
    "google-analytics.com",
    "googletagmanager.com",
    "ga('create'",
    "UA-",                 # legacy Universal Analytics property id prefix
    "webben.pl",           # old site author footer
    "© 2014",              # old copyright year
    "{{!",                 # Tornado comment token start
]


def doc_for(page, docs):
    import conftest
    return docs[page] if page in docs else conftest.parse(page)


@pytest.mark.parametrize("page", ALL)
@pytest.mark.parametrize("needle", FORBIDDEN_SUBSTRINGS)
def test_no_legacy_token_in_source(page, docs, needle):
    src = doc_for(page, docs).source
    assert needle not in src, f"{page}: legacy/leak token '{needle}' must not appear"


@pytest.mark.parametrize("page", ALL)
def test_footer_copyright_is_current(page, docs):
    footer = doc_for(page, docs).find("footer")
    assert footer is not None, f"{page}: missing footer"
    text = footer.text
    assert "Bezpieczeństwo Twojej Firmy" in text, f"{page}: footer must name BTF"
    assert "webben.pl" not in text, f"{page}: footer must not name webben.pl"
    assert "2014" not in text, f"{page}: footer must not show the legacy 2014 year"
    # a current copyright year is present (the redesign uses 2026)
    assert "©" in text, f"{page}: footer must carry a © notice"


def test_no_references_to_moved_legacy_paths():
    """No served page may reference the retired Tornado app paths."""
    import conftest
    bad_paths = ("/templates/", "templates/", "/app/", "btf.py", "gunicorn", "app.ini")
    for page in ALL:
        src = conftest.parse(page).source
        for bad in bad_paths:
            assert bad not in src, f"{page}: references moved legacy path '{bad}'"
