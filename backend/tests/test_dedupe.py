from app.utils.dedupe import compute_dedupe, is_duplicate


def test_dedupe_by_url_and_hash() -> None:
    result = compute_dedupe("Title", "Content", ["Other"], "https://example.com?utm_source=a")
    assert result.canonical_url == "https://example.com"
    assert result.hash_value
    assert not is_duplicate(result, ["https://other.com"], ["other"]) 


def test_dedupe_similarity() -> None:
    result = compute_dedupe("Breaking News", "Content", ["Breaking News"], "https://example.com")
    assert result.title_similarity >= 92
    assert is_duplicate(result, [], [])
