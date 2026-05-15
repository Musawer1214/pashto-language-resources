from scripts.check_links import md_files


def test_md_files_skips_local_artifact_directories(tmp_path) -> None:
    keep = tmp_path / "docs" / "README.md"
    keep.parent.mkdir(parents=True)
    keep.write_text("[Example](https://example.org)\n", encoding="utf-8")

    ignored = tmp_path / "output" / "repo-inspect" / "README.md"
    ignored.parent.mkdir(parents=True)
    ignored.write_text("https://example.org/raw\n", encoding="utf-8")

    assert md_files(tmp_path) == [keep]
