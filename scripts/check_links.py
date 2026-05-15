"""Validate markdown links across the repository.

Checks:
1. Reject non-clickable URL formatting such as `https://...` inside backticks.
2. Reject raw bare URLs that are not markdown links.
3. Optionally verify remote URL reachability with --online.

Usage:
    python scripts/check_links.py
    python scripts/check_links.py --online
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+)\)")
HTML_ATTR_URL_RE = re.compile(r"""(?:href|src|content)=["'](https?://[^"']+)["']""")
CSS_URL_RE = re.compile(r"""url\(["']?(https?://[^"')]+)["']?\)""")
CODE_URL_RE = re.compile(r"`(https?://[^`\s]+)`")
RAW_URL_RE = re.compile(r"""https?://[^\s)>\]"']+""")
IGNORED_DIRS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "artifacts",
    "build",
    "checkpoints",
    "dist",
    "output",
    "outputs",
    "test-results",
}


def md_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if not any(part in IGNORED_DIRS for part in path.relative_to(root).parts[:-1])
    )


def lint_markdown_links(path: Path) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    urls: set[str] = set()
    lines = path.read_text(encoding="utf-8").splitlines()

    for line_no, line in enumerate(lines, start=1):
        for match in MARKDOWN_LINK_RE.finditer(line):
            urls.add(match.group(1))
        for match in HTML_ATTR_URL_RE.finditer(line):
            urls.add(match.group(1))
        for match in CSS_URL_RE.finditer(line):
            urls.add(match.group(1))

        for match in CODE_URL_RE.finditer(line):
            errors.append(
                f"{path}:{line_no} non-clickable code URL; use markdown link: {match.group(1)}"
            )

        for raw in RAW_URL_RE.finditer(line):
            url = raw.group(0)
            start = raw.start()
            end = raw.end()

            # Skip URLs that are part of markdown links.
            if start >= 1 and line[start - 1] == "(":
                continue
            if end < len(line) and line[end : end + 1] == ")":
                continue

            # Skip URLs inside HTML attributes in markdown files that use
            # layout: null with full HTML bodies.
            prefix = line[max(0, start - 24) : start].lower()
            if prefix.endswith(
                ('href="', "href='", 'src="', "src='", 'content="', "content='", 'url("', "url('", "url(")
            ):
                continue

            # Skip URLs inside backticks (already handled above).
            if (start >= 1 and line[start - 1] == "`") or (
                end < len(line) and line[end : end + 1] == "`"
            ):
                continue

            errors.append(f"{path}:{line_no} bare URL; wrap in markdown link: {url}")

    return errors, urls


def check_url_online(url: str, timeout: float = 10.0) -> str | None:
    request = Request(url, method="HEAD", headers={"User-Agent": "pashto-link-checker/1.0"})
    try:
        with urlopen(request, timeout=timeout):
            return None
    except HTTPError as exc:
        if exc.code in {403, 405}:
            # Some hosts block HEAD; retry with GET.
            pass
        else:
            return f"{url} returned HTTP {exc.code}"
    except URLError as exc:
        return f"{url} failed: {exc.reason}"
    except TimeoutError:
        return f"{url} failed: timeout"

    request = Request(url, method="GET", headers={"User-Agent": "pashto-link-checker/1.0"})
    try:
        with urlopen(request, timeout=timeout):
            return None
    except HTTPError as exc:
        return f"{url} returned HTTP {exc.code}"
    except URLError as exc:
        return f"{url} failed: {exc.reason}"
    except TimeoutError:
        return f"{url} failed: timeout"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--online", action="store_true", help="Check URL reachability online")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = md_files(root)
    all_errors: list[str] = []
    all_urls: set[str] = set()

    for path in files:
        errors, urls = lint_markdown_links(path)
        all_errors.extend(errors)
        all_urls.update(urls)

    if args.online:
        for url in sorted(all_urls):
            error = check_url_online(url)
            if error:
                all_errors.append(f"URL check failed: {error}")

    if all_errors:
        print("Link check failed:")
        for error in all_errors:
            print(f"- {error}")
        return 1

    print(f"Link check passed: {len(files)} markdown files, {len(all_urls)} URLs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
