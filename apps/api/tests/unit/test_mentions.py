"""Unit tests for @mention parsing utilities."""

from __future__ import annotations

from app.services.mention_service import parse_mentions


class TestParseMentions:
    def test_empty(self):
        assert parse_mentions("") == []

    def test_start_of_string(self):
        assert parse_mentions("@Alice") == ["Alice"]

    def test_requires_whitespace_before_at(self):
        assert parse_mentions("hi@Bob") == []
        assert parse_mentions("email test@foo.com") == []

    def test_space_before_at_matches(self):
        assert parse_mentions("hi @Bob") == ["Bob"]

    def test_newline_before_at_matches(self):
        # Whitespace includes newlines, tabs, etc.
        assert parse_mentions("hi\n@Bob") == ["Bob"]

    def test_parenthesis_before_at_does_not_match(self):
        assert parse_mentions("(@Bob)") == []

    def test_case_insensitive_dedup_preserves_first_spelling(self):
        assert parse_mentions("@Alice hi @alice @ALICE") == ["Alice"]

    def test_hard_max_length_50(self):
        ok = "a" * 50
        too_long = "b" * 51
        assert parse_mentions(f"@{ok}") == [ok]
        assert parse_mentions(f"@{too_long}") == []
