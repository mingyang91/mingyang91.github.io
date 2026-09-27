#!/usr/bin/env python3
"""Check the built site's local links, anchors, and assets without network access."""

import argparse
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import unquote, urljoin, urlsplit


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "name" in attrs:
            self.ids.add(attrs["name"])
        for key in ("href", "src", "poster"):
            if attrs.get(key):
                self.links.append((attrs[key], tag == "a"))
        if tag in ("img", "source") and attrs.get("srcset"):
            self.links.extend((part.strip().split()[0], False) for part in attrs["srcset"].split(",") if part.strip())


def check(root, base_url):
    origin = urlsplit(base_url).netloc
    pages = {file.relative_to(root).as_posix(): Page(file.read_text()) for file in root.rglob("*.html")}
    failures = []
    checked = 0
    for path, page in pages.items():
        page_url = urljoin(base_url, path.removesuffix("index.html"))
        for value, check_anchor in page.links:
            target_url = urlsplit(urljoin(page_url, value))
            if target_url.scheme not in ("http", "https") or target_url.netloc != origin:
                continue
            target = unquote(target_url.path).lstrip("/")
            file = root / target
            if file.is_dir():
                file = file / "index.html"
            checked += 1
            if not file.is_file():
                failures.append(f"{path}: missing target {value}")
                continue
            fragment = unquote(target_url.fragment)
            relative = file.relative_to(root).as_posix()
            if check_anchor and fragment and relative in pages and fragment not in pages[relative].ids:
                failures.append(f"{path}: missing anchor {value}")
    for failure in failures:
        print(failure, file=sys.stderr)
    print(f"Checked {len(pages)} HTML pages and {checked} local links/assets; {len(failures)} failures.")
    return bool(failures)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("public"))
    parser.add_argument("--base-url", default="https://famer.me/")
    args = parser.parse_args()
    if not (args.root / "index.html").is_file():
        parser.error(f"{args.root} does not contain a built site")
    sys.exit(check(args.root, args.base_url))
