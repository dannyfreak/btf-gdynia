"""Pytest harness for the static BTF site.

All tests verify the public surface only: the static HTML/CSS/JS served from the
repo root. HTML is parsed with the Python stdlib ``html.parser`` (no third-party
HTML library). CSS/XML are read as plain text or parsed with stdlib only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Repo locations
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent

PAGES = ["index.html", "uslugi.html", "oferta.html", "cennik.html", "kontakt.html"]

# Canonical domain (GitHub Pages custom domain).
DOMAIN = "https://btf-gdynia.pl/"


def page_path(name: str) -> Path:
    return REPO_ROOT / name


def read_text(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Minimal DOM built from stdlib html.parser
# ---------------------------------------------------------------------------
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    parent: "Node | None" = None
    _text_parts: list = field(default_factory=list)

    # -- traversal helpers --------------------------------------------------
    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def find_all(self, tag):
        return [n for n in self.walk() if n.tag == tag]

    def find(self, tag):
        for n in self.walk():
            if n.tag == tag:
                return n
        return None

    @property
    def text(self) -> str:
        """Concatenated visible text of this node and descendants."""
        out = []
        for n in self.walk():
            for part in n._text_parts:
                out.append(part)
        return " ".join(" ".join(out).split())

    def has_class(self, *names) -> bool:
        classes = set(self.attrs.get("class", "").split())
        return any(name in classes for name in names)

    @property
    def element_children(self):
        return list(self.children)


class _DOMBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node(tag="#root")
        self.stack = [self.root]
        # Tags we deliberately skip nesting bookkeeping for content extraction.
        self.skip_content = None

    def handle_starttag(self, tag, attrs):
        node = Node(tag=tag, attrs=dict(attrs), parent=self.stack[-1])
        self.stack[-1].children.append(node)
        if tag in ("script", "style"):
            self.skip_content = tag
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag=tag, attrs=dict(attrs), parent=self.stack[-1])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        if tag == self.skip_content:
            self.skip_content = None
        if tag in VOID_TAGS:
            return
        # Pop back to the matching open tag if present.
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.skip_content:
            return
        text = data.strip()
        if text:
            self.stack[-1]._text_parts.append(text)


@dataclass
class Document:
    name: str
    source: str
    root: Node

    def find_all(self, tag):
        return self.root.find_all(tag)

    def find(self, tag):
        return self.root.find(tag)

    @property
    def text(self) -> str:
        return self.root.text

    def find_html(self) -> Node | None:
        return self.find("html")


def parse(name: str) -> Document:
    source = read_text(name)
    builder = _DOMBuilder()
    builder.feed(source)
    builder.close()
    return Document(name=name, source=source, root=builder.root)


# ---------------------------------------------------------------------------
# href / link resolution helpers
# ---------------------------------------------------------------------------
def strip_fragment(href: str) -> str:
    return href.split("#", 1)[0]


def resolves_to(href: str, target: str) -> bool:
    """True if a relative href points at ``target`` (ignoring #fragment).

    Accepts both the bare ``target`` and a ``./``-prefixed form.
    """
    base = strip_fragment(href).strip()
    return base == target or base == "./" + target


def is_relative(href: str) -> bool:
    h = href.strip()
    if h.startswith(("http://", "https://", "tel:", "mailto:", "/", "#",
                     "data:", "javascript:")):
        return False
    return True


# Emoji detection: cover the common pictographic ranges.
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F000-\U0001F0FF"
    "\U00002190-\U000021FF"  # arrows sometimes abused as icons
    "\U00002B00-\U00002BFF"
    "️"  # variation selector
    "]"
)


def contains_emoji(text: str) -> bool:
    return bool(_EMOJI_RE.search(text))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def docs() -> dict:
    return {name: parse(name) for name in PAGES}
