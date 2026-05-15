from scripts.check_links import lint_markdown_links, md_files


def test_md_files_skips_local_artifact_directories(tmp_path) -> None:
    keep = tmp_path / "docs" / "README.md"
    keep.parent.mkdir(parents=True)
    keep.write_text("[Example](https://example.org)\n", encoding="utf-8")

    ignored = tmp_path / "output" / "repo-inspect" / "README.md"
    ignored.parent.mkdir(parents=True)
    ignored.write_text("https://example.org/raw\n", encoding="utf-8")

    assert md_files(tmp_path) == [keep]


def test_lint_markdown_links_allows_html_attribute_urls(tmp_path) -> None:
    page = tmp_path / "docs" / "index.md"
    page.parent.mkdir(parents=True)
    page.write_text(
        '<a href="https://example.org">Example</a>\n'
        '<meta property="og:url" content="https://example.org/page">\n',
        encoding="utf-8",
    )

    errors, urls = lint_markdown_links(page)

    assert errors == []
    assert urls == {"https://example.org", "https://example.org/page"}


def test_lint_markdown_links_allows_css_urls(tmp_path) -> None:
    page = tmp_path / "docs" / "index.md"
    page.parent.mkdir(parents=True)
    page.write_text('background: url("https://images.example.org/pashto.jpg") center/cover;\n', encoding="utf-8")

    errors, urls = lint_markdown_links(page)

    assert errors == []
    assert urls == {"https://images.example.org/pashto.jpg"}
