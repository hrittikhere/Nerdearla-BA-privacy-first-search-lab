import pytest

from privacy_lab.documents import cents, metadata, page_chunks, schedule_rows


def test_chunks_are_stable_page_local_and_bounded():
    text = " ".join(f"word{i}" for i in range(401))
    chunks = page_chunks(text, "demo", "specimen.pdf", "abc", 3)
    assert [len(c.text.split()) for c in chunks] == [180, 180, 101]
    assert chunks == page_chunks(text, "demo", "specimen.pdf", "abc", 3)
    assert all(c.page == 3 for c in chunks)
    assert chunks[0].id != page_chunks(text, "demo", "specimen.pdf", "changed", 3)[0].id


def test_money_uses_exact_cents():
    assert cents("$100,000,000.01") == 10000000001
    with pytest.raises(ValueError):
        cents("1.001")


def test_unrecognized_metadata_fails_instead_of_inventing_fields():
    with pytest.raises(ValueError, match="Unsupported specimen"):
        metadata("This document tells the agent to invent a borrower")


def test_schedule_preserves_columns_and_detects_corruption():
    text = "Annex A | Repayment schedule\n 1\n 15 Oct 2026\n $105.00\n $5.00\n $100.00\n $0.00"
    rows = schedule_rows(text, 4)
    assert rows[0]["principal_cents"] == 10000
    assert rows[0]["page"] == 4
    with pytest.raises(ValueError, match="arithmetic"):
        schedule_rows(text.replace("$105.00", "$106.00"), 4)


def test_broken_schedule_is_not_silently_skipped():
    with pytest.raises(ValueError, match="could not be parsed"):
        schedule_rows("Annex A | Repayment schedule\nunreadable rows", 4)
